"""
Chat Service
Handles Q&A conversations about research papers using LLM.
"""
import json
import logging
import os
from typing import List, Dict, Optional, Tuple
from ..core.config import settings

# New chat implementation: RAG over the paper using Pinecone + LangChain.
# Keeps the same public function signature (`ask_about_paper`) so existing
# route imports do not need to change.

# LangChain / Pinecone imports (installed via backend/requirements.txt)
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from langchain_classic.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from upstash_redis import Redis


INDEX_NAME = settings.PINECONE_INDEX_NAME or os.getenv("PINECONE_INDEX_NAME", "research-flow-index")
EMBEDDING_MODEL_NAME = settings.OPENAI_EMBEDDING_MODEL or os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
CHAT_SESSION_PREFIX = "chat_session:"
FALLBACK_MEMORY_SESSIONS: Dict[str, List[Dict[str, str]]] = {}


def _require_env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise ValueError(f"{name} not configured")
    return val


def _get_models(chat_model: str) -> Tuple[OpenAIEmbeddings, ChatOpenAI]:
    # ChatOpenAI/OpenAIEmbeddings rely on OPENAI_API_KEY in env.
    # Keep compatibility with existing settings loader.
    if settings.OPENAI_API_KEY and not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL_NAME)
    llm = ChatOpenAI(model=chat_model, temperature=0)
    return embeddings, llm


def _get_pinecone() -> Pinecone:
    api_key = settings.PINECONE_API_KEY or os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY not configured")
    # Some integrations read from process env internally; keep it synced.
    if not os.getenv("PINECONE_API_KEY"):
        os.environ["PINECONE_API_KEY"] = api_key
    return Pinecone(api_key=api_key)


def _get_redis_client() -> Optional[Redis]:
    """
    Build Upstash Redis client when configured.
    Returns None when Redis env vars are absent, allowing memory fallback.
    """
    redis_url = settings.UPSTASH_REDIS_REST_URL or os.getenv("UPSTASH_REDIS_REST_URL")
    redis_token = settings.UPSTASH_REDIS_REST_TOKEN or os.getenv("UPSTASH_REDIS_REST_TOKEN")
    if not redis_url or not redis_token:
        return None
    return Redis(url=redis_url, token=redis_token)


def _session_key(session_id: str) -> str:
    return f"{CHAT_SESSION_PREFIX}{session_id}"


def load_session(session_id: str) -> List[Dict[str, str]]:
    """
    Load chat history from Upstash Redis.
    Falls back to in-memory store when Redis is not configured.
    """
    if not session_id or not session_id.strip():
        return []

    redis_client = _get_redis_client()
    if redis_client is None:
        return FALLBACK_MEMORY_SESSIONS.get(session_id, []).copy()

    raw = redis_client.get(_session_key(session_id))
    if raw is None:
        return []

    try:
        if isinstance(raw, str):
            parsed = json.loads(raw)
        elif isinstance(raw, list):
            parsed = raw
        else:
            parsed = json.loads(str(raw))
        if isinstance(parsed, list):
            return [m for m in parsed if isinstance(m, dict)]
    except Exception:
        logging.warning("Failed to parse session history for %s", session_id, exc_info=True)
    return []


def save_session(session_id: str, history: List[Dict[str, str]]) -> None:
    """
    Save full chat history with TTL.
    """
    if not session_id or not session_id.strip():
        return

    ttl = int(getattr(settings, "REDIS_CHAT_TTL", 3600) or 3600)
    redis_client = _get_redis_client()
    if redis_client is None:
        FALLBACK_MEMORY_SESSIONS[session_id] = history.copy()
        return

    payload = json.dumps(history, ensure_ascii=True)
    redis_client.set(_session_key(session_id), payload, ex=ttl)


def delete_session(session_id: str) -> None:
    """
    Delete a chat session.
    """
    if not session_id or not session_id.strip():
        return

    redis_client = _get_redis_client()
    if redis_client is None:
        FALLBACK_MEMORY_SESSIONS.pop(session_id, None)
        return
    redis_client.delete(_session_key(session_id))


def _ensure_index(pc: Pinecone) -> None:
    # dimension must match text-embedding-3-small output (1536)
    # If you change EMBEDDING_MODEL_NAME, also update dimension accordingly.
    if INDEX_NAME in pc.list_indexes().names():
        return
    pc.create_index(
        name=INDEX_NAME,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud=os.getenv("PINECONE_CLOUD", "aws"), region=os.getenv("PINECONE_REGION", "us-east-1")),
    )
    logging.info(f"Pinecone index '{INDEX_NAME}' created")


def _paper_namespace(paper_text: str) -> str:
    import hashlib

    sha = hashlib.sha256()
    sha.update(paper_text.encode("utf-8", errors="ignore"))
    return sha.hexdigest()


def _split_to_documents(
    paper_text: str,
    paper_id: str,
    paper_title: Optional[str] = None,
    paper_source: Optional[str] = None,
) -> List[Document]:
    # Build a single Document then split into chunked Documents
    meta = {"paper_id": paper_id}
    if paper_title:
        meta["paper_title"] = paper_title
    base = Document(page_content=paper_text, metadata=meta)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=80,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks = splitter.split_documents([base])
    for c in chunks:
        c.metadata.update(meta)
    return chunks


def _stable_chunk_ids(chunks: List[Document], paper_id: str) -> List[str]:
    # Use deterministic IDs so re-ingesting the same paper doesn't create duplicates.
    import hashlib

    ids: List[str] = []
    for i, d in enumerate(chunks):
        h = hashlib.sha256()
        h.update(paper_id.encode("utf-8"))
        h.update(b"\n")
        h.update(d.page_content.encode("utf-8", errors="ignore"))
        ids.append(f"{paper_id[:12]}-{i}-{h.hexdigest()[:24]}")
    return ids


def _to_langchain_messages(conversation_history: Optional[List[Dict[str, str]]]) -> List[BaseMessage]:
    if not conversation_history:
        return []
    msgs: List[BaseMessage] = []
    for m in conversation_history:
        role = (m.get("role") or "").lower()
        content = m.get("content") or ""
        if not content:
            continue
        if role == "user":
            msgs.append(HumanMessage(content=content))
        elif role == "assistant":
            msgs.append(AIMessage(content=content))
        elif role == "system":
            msgs.append(SystemMessage(content=content))
        else:
            # Unknown role → treat as user content
            msgs.append(HumanMessage(content=content))
    return msgs


def ask_about_paper(
    question: str,
    paper_text: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    model: str = "gpt-4o-mini",
    paper_title: Optional[str] = None,
    paper_source: Optional[str] = None,
) -> Optional[str]:
    """
    Answer a question about a research paper using RAG (Pinecone retrieval over paper chunks).
    
    Args:
        question: User's question about the paper
        paper_text: Full extracted text of the paper
        conversation_history: Previous messages in the conversation (optional)
        model: Chat model to use (default: gpt-4o-mini)
        paper_title: Title of the paper (stored in Pinecone metadata)
        paper_source: Source of the paper e.g. arXiv, CORE, PMC (stored in Pinecone metadata)
    
    Returns:
        LLM's answer as a string, or None if error
    """
    if not question or not question.strip():
        logging.warning("Empty question provided")
        raise ValueError("Empty question provided")
    
    if not paper_text or len(paper_text.strip()) < 100:
        logging.warning("Paper text too short or empty")
        raise ValueError("Paper text too short or empty for Q&A")

    try:
        # Ensure credentials exist early with a clear error
        if not (settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")):
            raise ValueError("OPENAI_API_KEY not configured")

        embeddings, llm = _get_models(model)

        pinecone_api_key = settings.PINECONE_API_KEY or os.getenv("PINECONE_API_KEY")
        if not pinecone_api_key:
            raise ValueError("PINECONE_API_KEY not configured")

        pc = _get_pinecone()
        _ensure_index(pc)

        paper_id = _paper_namespace(paper_text)

        # Build/Update namespace vectorstore for this paper
        vectorstore = PineconeVectorStore(
            index_name=INDEX_NAME,
            embedding=embeddings,
            namespace=paper_id,
            pinecone_api_key=pinecone_api_key,
        )

        chunks = _split_to_documents(paper_text, paper_id, paper_title=paper_title, paper_source=paper_source)
        ids = _stable_chunk_ids(chunks, paper_id)
        # Upsert deterministically (safe to call multiple times)
        vectorstore.add_documents(chunks, ids=ids)

        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": int(os.getenv("RAG_TOP_K", "3")),
                "filter": {"paper_id": {"$eq": paper_id}},
            },
        )

        condensed_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Given the conversation history and a follow-up question, rephrase the follow-up question to be a standalone question. "
                    "If it is already standalone, return it as-is. Do NOT answer it — only rephrase.",
                ),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        history_aware_retriever = create_history_aware_retriever(llm, retriever, condensed_prompt)

        answer_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Answer using only the context below. If the answer is not found, say 'Not found in the document.'\n\nContext: {context}",
                ),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        document_chain = create_stuff_documents_chain(llm, answer_prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever, document_chain)

        chat_history_msgs = _to_langchain_messages(conversation_history)

        result = rag_chain.invoke(
            {
                "input": question.strip(),
                "chat_history": chat_history_msgs,
            }
        )

        answer = result.get("answer")
        if not isinstance(answer, str):
            answer = str(answer) if answer is not None else ""
        return answer.strip() if answer else None

    except ValueError:
        raise
    except Exception as e:
        logging.error(f"Error in chat service: {str(e)}", exc_info=True)
        raise ValueError(f"Chat error: {str(e)}")


def ask_about_paper_with_session(
    session_id: str,
    question: str,
    paper_text: str,
    model: str = "gpt-4o-mini",
    paper_title: Optional[str] = None,
    paper_source: Optional[str] = None,
) -> Optional[str]:
    """
    Ask about paper while persisting conversation history by session_id.
    """
    history = load_session(session_id)
    answer = ask_about_paper(
        question=question,
        paper_text=paper_text,
        conversation_history=history,
        model=model,
        paper_title=paper_title,
        paper_source=paper_source,
    )
    if answer:
        updated_history = history + [
            {"role": "user", "content": question.strip()},
            {"role": "assistant", "content": answer},
        ]
        save_session(session_id, updated_history)
    return answer