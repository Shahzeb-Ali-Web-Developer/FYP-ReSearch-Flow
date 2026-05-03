"""
Chat Service
Handles Q&A conversations about research papers using LLM + Pinecone RAG.
"""
import hashlib
import json
import logging
import os
import time
from typing import List, Dict, Optional, Tuple

from ..core.config import settings

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from langchain_classic.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore


INDEX_NAME = settings.PINECONE_INDEX_NAME
EMBEDDING_MODEL_NAME = settings.OPENAI_EMBEDDING_MODEL

# In-memory set tracking which paper_ids are already indexed in Pinecone.
# Prevents calling add_documents on every question — the root cause of "Not found".
# Resets on server restart (acceptable: first question per paper re-checks Pinecone).
_indexed_paper_ids: set = set()

# In-memory store of raw (pre-contextual) chunks per paper for BM25 keyword retrieval.
# BM25 is exact keyword matching — it catches what semantic search misses.
# Stored as plain text strings; rebuilt from Pinecone on server restart if needed.
_paper_chunks_cache: Dict[str, List[Document]] = {}

# Fallback chat sessions when Upstash Redis is not configured (dev / single-worker).
_memory_chat_sessions: Dict[str, Tuple[List[Dict[str, str]], float]] = {}


def _use_contextual_chunk_prefix() -> bool:
    """
    If true: one LLM call per chunk at index time (slow for long papers; first answer can take many minutes).
    Default false: index raw chunks only — fast; hybrid BM25 + semantic retrieval still works well.
    Set env CHAT_CONTEXTUAL_CHUNK_PREFIX=1 to enable the slower enrichment.
    """
    v = (os.getenv("CHAT_CONTEXTUAL_CHUNK_PREFIX") or "").strip().lower()
    return v in ("1", "true", "yes")


# ── Internal helpers ───────────────────────────────────────────────────────

def _get_models(chat_model: str) -> Tuple[OpenAIEmbeddings, ChatOpenAI]:
    if settings.OPENAI_API_KEY and not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL_NAME)
    llm = ChatOpenAI(model=chat_model, temperature=0)
    return embeddings, llm


def _resolve_pinecone_api_key() -> str:
    """Key from process env or pydantic-loaded .env (Settings does not set os.environ)."""
    key = (os.getenv("PINECONE_API_KEY") or (settings.PINECONE_API_KEY or "")).strip()
    if not key:
        raise ValueError("PINECONE_API_KEY not configured")
    return key


def _get_pinecone() -> Pinecone:
    api_key = _resolve_pinecone_api_key()
    # LangChain PineconeVectorStore reads PINECONE_API_KEY from the environment only
    # unless pinecone_api_key= is passed; keep env in sync with Settings/.env.
    os.environ["PINECONE_API_KEY"] = api_key
    return Pinecone(api_key=api_key)


def _ensure_index(pc: Pinecone) -> None:
    """Create Pinecone index if it does not already exist."""
    if INDEX_NAME in pc.list_indexes().names():
        return
    pc.create_index(
        name=INDEX_NAME,
        dimension=1536,    # must match text-embedding-3-small
        metric="cosine",
        spec=ServerlessSpec(
            cloud=os.getenv("PINECONE_CLOUD", "aws"),
            region=os.getenv("PINECONE_REGION", "us-east-1")
        ),
    )
    logging.info(f"Pinecone index '{INDEX_NAME}' created")


def _make_paper_id(paper_text: str) -> str:
    """
    Derive a stable short ID from paper text.
    Use first 40 chars of SHA256 — well within Pinecone's namespace limit.
    """
    sha = hashlib.sha256()
    sha.update(paper_text.encode("utf-8", errors="ignore"))
    return sha.hexdigest()[:40]


def make_paper_id(paper_text: str) -> str:
    """Stable paper id (same as Pinecone namespace) — first 40 hex chars of SHA256 of full text."""
    return _make_paper_id(paper_text)


def _add_context_to_chunk(chunk: Document, full_paper: str, llm: ChatOpenAI) -> Document:
    """
    Contextual embeddings: prepend an AI-generated description of where this
    chunk sits in the paper before embedding it.

    This dramatically improves retrieval for vague or follow-up questions
    (e.g. "how did it perform?") because the embedding now captures section
    context, not just raw text.

    One LLM call per chunk at index time — no extra cost at query time.
    """
    # Truncate paper to stay within token budget (first 3000 chars is enough
    # for the model to understand structure without hitting limits)
    paper_preview = full_paper[:3000]

    prompt = (
        "You are helping index a research paper for retrieval.\n\n"
        f"Here is an overview of the paper:\n<paper>\n{paper_preview}\n</paper>\n\n"
        f"Here is a specific chunk from that paper:\n<chunk>\n{chunk.page_content}\n</chunk>\n\n"
        "Write 2-3 sentences describing:\n"
        "1. Which section of the paper this chunk belongs to (e.g. Abstract, Introduction, "
        "Methodology, Results, Conclusion, References).\n"
        "2. What specific concept or finding this chunk covers.\n\n"
        "Be concise and factual. Output ONLY the description — no preamble, "
        "no labels, no extra formatting."
    )

    try:
        response = llm.invoke(prompt)
        context_prefix = response.content.strip()
        contextualized_text = f"{context_prefix}\n---\n{chunk.page_content}"
        return Document(page_content=contextualized_text, metadata=chunk.metadata)
    except Exception as e:
        # If LLM call fails for any chunk, fall back to the original chunk
        # so indexing is not blocked entirely
        logging.warning(f"Context generation failed for chunk, using original: {e}")
        return chunk


def _split_to_documents(
    paper_text: str,
    paper_id: str,
    llm: ChatOpenAI,
    paper_title: Optional[str] = None,
    paper_source: Optional[str] = None,
) -> Tuple[List[Document], List[Document]]:
    """
    Split paper text into chunks and attach metadata.

    Optionally (CHAT_CONTEXTUAL_CHUNK_PREFIX=1) prepends an LLM summary per chunk
    for Pinecone; default is plain chunks only so the first question returns quickly.

    Returns:
        raw_chunks:            Original chunks (BM25 keyword retrieval)
        contextualized_chunks: Chunks for Pinecone vector indexing
    """
    meta = {"paper_id": paper_id}
    if paper_title:
        meta["paper_title"] = paper_title
    if paper_source:
        meta["paper_source"] = paper_source

    base = Document(page_content=paper_text, metadata=meta)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""],
    )
    raw_chunks = splitter.split_documents([base])
    for c in raw_chunks:
        c.metadata.update(meta)

    n = len(raw_chunks)
    if _use_contextual_chunk_prefix():
        logging.info("Contextual chunk prefixes enabled: %s LLM calls at index time...", n)
        contextualized_chunks = [
            _add_context_to_chunk(chunk, paper_text, llm)
            for chunk in raw_chunks
        ]
        logging.info("Contextual prefix generation complete.")
    else:
        logging.info(
            "Indexing %s chunks without per-chunk LLM (fast). "
            "Set CHAT_CONTEXTUAL_CHUNK_PREFIX=1 for slower, enriched embeddings.",
            n,
        )
        contextualized_chunks = [
            Document(page_content=c.page_content, metadata=dict(c.metadata))
            for c in raw_chunks
        ]
    return raw_chunks, contextualized_chunks


def _stable_chunk_ids(chunks: List[Document], paper_id: str) -> List[str]:
    """
    Deterministic chunk IDs — safe to upsert multiple times without creating duplicates.
    """
    ids: List[str] = []
    for i, d in enumerate(chunks):
        h = hashlib.sha256()
        h.update(paper_id.encode("utf-8"))
        h.update(b"\n")
        h.update(d.page_content.encode("utf-8", errors="ignore"))
        ids.append(f"{paper_id[:12]}-{i}-{h.hexdigest()[:24]}")
    return ids


def _is_paper_indexed(pc: Pinecone, paper_id: str) -> bool:
    """
    Check Pinecone to see if this paper's namespace already has vectors.
    Used to skip re-indexing on every question.
    """
    try:
        index = pc.Index(INDEX_NAME)
        stats = index.describe_index_stats()
        namespaces = stats.get("namespaces", {})
        ns = namespaces.get(paper_id, {})
        count = ns.get("vector_count", 0)
        return count > 0
    except Exception as e:
        logging.warning(f"Could not check index stats: {e}")
        return False   # if unsure, re-index to be safe


def _wait_for_indexing(
    pc: Pinecone,
    paper_id: str,
    expected_count: int,
    timeout: Optional[int] = None,
) -> None:
    """
    Poll Pinecone until the expected number of vectors appear in the namespace,
    or until timeout is reached.

    FIX: Replaces the fragile time.sleep(3) approach. A fixed sleep races
    against Pinecone's async upsert — under load or network lag it fires
    the query before vectors are ready, causing "Not found in the document".

    This poll loop checks every second and only proceeds once vectors are
    confirmed present, with a generous but bounded timeout.
    """
    if timeout is None:
        # Serverless stats can lag; scale with batch size (cap 5 min).
        timeout = min(300, max(45, 35 + expected_count * 2))
    index = pc.Index(INDEX_NAME)
    deadline = time.time() + timeout
    last_count = 0

    logging.info(
        f"Waiting for Pinecone to index {expected_count} vectors "
        f"in namespace '{paper_id[:12]}' (timeout={timeout}s)..."
    )

    while time.time() < deadline:
        try:
            stats = index.describe_index_stats()
            ns = stats.get("namespaces", {}).get(paper_id, {})
            last_count = ns.get("vector_count", 0)
            if last_count >= expected_count:
                logging.info(
                    f"Pinecone ready: {last_count}/{expected_count} vectors confirmed."
                )
                return
        except Exception as e:
            logging.warning(f"Poll error while waiting for indexing: {e}")

        time.sleep(1)

    # Timeout reached — log a warning but do not crash. Retrieval may still
    # partially succeed, and the in-memory cache will prevent re-indexing.
    logging.warning(
        f"Pinecone indexing timed out after {timeout}s. "
        f"Got {last_count}/{expected_count} vectors. Proceeding anyway."
    )


def _index_paper(
    vectorstore: PineconeVectorStore,
    pc: Pinecone,
    paper_text: str,
    paper_id: str,
    llm: ChatOpenAI,
    paper_title: Optional[str],
    paper_source: Optional[str],
) -> None:
    """
    Index paper into Pinecone ONLY if not already indexed.

    Uses a poll loop (not sleep) to wait for vectors to be ready,
    and enriches each chunk with contextual embeddings before upsert.
    """
    global _indexed_paper_ids

    # Fast path: already confirmed indexed this session
    if paper_id in _indexed_paper_ids:
        logging.debug(f"Paper {paper_id[:12]} already indexed (cached). Skipping upsert.")
        return

    # Slower path: check Pinecone directly
    if _is_paper_indexed(pc, paper_id):
        logging.info(f"Paper {paper_id[:12]} found in Pinecone. Skipping upsert.")
        _indexed_paper_ids.add(paper_id)
        return

    # Paper not indexed yet — upload now
    logging.info(f"Indexing paper {paper_id[:12]} into Pinecone...")

    # _split_to_documents returns raw chunks (for BM25) and contextualized chunks (for Pinecone)
    raw_chunks, contextualized_chunks = _split_to_documents(
        paper_text,
        paper_id,
        llm=llm,
        paper_title=paper_title,
        paper_source=paper_source,
    )
    ids = _stable_chunk_ids(contextualized_chunks, paper_id)
    vectorstore.add_documents(contextualized_chunks, ids=ids)

    # Cache raw chunks for BM25 keyword retrieval (never the contextualized ones —
    # BM25 needs clean original text for exact keyword matching)
    _paper_chunks_cache[paper_id] = raw_chunks

    # Poll until Pinecone confirms all vectors are ready (replaces sleep)
    _wait_for_indexing(pc, paper_id, expected_count=len(contextualized_chunks))

    _indexed_paper_ids.add(paper_id)
    logging.info(f"Paper {paper_id[:12]} indexed successfully ({len(contextualized_chunks)} chunks)")


def _to_langchain_messages(
    conversation_history: Optional[List[Dict[str, str]]]
) -> List[BaseMessage]:
    """Convert conversation history dicts to LangChain message objects."""
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
            msgs.append(HumanMessage(content=content))
    return msgs


def _build_rag_chain(llm: ChatOpenAI, retriever, has_history: bool):
    """
    Build the RAG pipeline.

    FIX: The history-aware retriever rephrases queries through the LLM before
    retrieval. For the first question (empty history) this adds latency and
    can subtly distort the query, reducing retrieval quality.

    Now: history-aware retriever is only activated when there is actual
    conversation history. First questions hit the retriever directly.

    Chain 1 (conditional) — history_aware_retriever:
        Rephrases follow-up questions into standalone questions using history.
        Skipped entirely when has_history=False.

    Chain 2 — document_chain:
        Answers using retrieved context chunks.
    """
    if has_history:
        # Rephrase follow-up into standalone question using history
        condensed_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "Given the conversation history and a follow-up question, "
                "rephrase the follow-up question to be a standalone question. "
                "If it is already standalone, return it as-is. "
                "Do NOT answer it — only rephrase.",
            ),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        effective_retriever = create_history_aware_retriever(llm, retriever, condensed_prompt)
        logging.debug("Using history-aware retriever (conversation history present).")
    else:
        # No history — use retriever directly, no extra LLM call needed
        effective_retriever = retriever
        logging.debug("Using direct retriever (no conversation history).")

    # Answer using retrieved chunks + optional history
    answer_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are a research assistant helping users understand a paper.\n"
            "Answer the question using the context below.\n"
            "- If the context clearly contains the answer, give a direct, detailed response.\n"
            "- If the context partially covers the question, answer what you can and note any gaps.\n"
            "- Only say 'Not found in the document' if the context has absolutely no relevant "
            "information — not just because the phrasing differs.\n\n"
            "Context:\n{context}",
        ),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    document_chain = create_stuff_documents_chain(llm, answer_prompt)

    return create_retrieval_chain(effective_retriever, document_chain)


# ── Chat session persistence (Upstash Redis or in-memory fallback) ───────

def _redis_client():
    url = settings.UPSTASH_REDIS_REST_URL
    token = settings.UPSTASH_REDIS_REST_TOKEN
    if not url or not token:
        return None
    try:
        from upstash_redis import Redis
        return Redis(url=url, token=token)
    except Exception as e:
        logging.warning("Upstash Redis unavailable: %s", e)
        return None


def _session_storage_key(session_id: str) -> str:
    return f"research-flow:paper-chat:{session_id}"


def load_session(session_id: str) -> List[Dict[str, str]]:
    """Return prior messages [{role, content}, ...] for this session."""
    if not session_id or not str(session_id).strip():
        return []
    sid = str(session_id).strip()
    client = _redis_client()
    if client:
        try:
            raw = client.get(_session_storage_key(sid))
            if raw is None:
                return []
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            data = json.loads(raw)
            if not isinstance(data, list):
                return []
            out: List[Dict[str, str]] = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                role = item.get("role") or ""
                content = item.get("content") or ""
                if content:
                    out.append({"role": str(role), "content": str(content)})
            return out
        except Exception as e:
            logging.warning("load_session Redis error: %s", e)
            return []

    now = time.time()
    entry = _memory_chat_sessions.get(sid)
    if not entry:
        return []
    messages, expires_at = entry
    if now > expires_at:
        _memory_chat_sessions.pop(sid, None)
        return []
    return list(messages)


def _save_session_messages(session_id: str, messages: List[Dict[str, str]]) -> None:
    sid = str(session_id).strip()
    ttl = max(60, int(settings.REDIS_CHAT_TTL))
    client = _redis_client()
    if client:
        try:
            client.set(_session_storage_key(sid), json.dumps(messages), ex=ttl)
        except Exception as e:
            logging.warning("save_session Redis error: %s", e)
        return
    _memory_chat_sessions[sid] = (list(messages), time.time() + ttl)


def delete_session(session_id: str) -> None:
    if not session_id or not str(session_id).strip():
        return
    sid = str(session_id).strip()
    client = _redis_client()
    if client:
        try:
            client.delete(_session_storage_key(sid))
        except Exception as e:
            logging.warning("delete_session Redis error: %s", e)
    _memory_chat_sessions.pop(sid, None)


# ── Public API ─────────────────────────────────────────────────────────────

def ask_about_paper(
    question: str,
    paper_text: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    model: str = "gpt-4o-mini",
    paper_title: Optional[str] = None,
    paper_source: Optional[str] = None,
) -> Optional[str]:
    """
    Answer a question about a research paper using RAG (Pinecone + LangChain).

    Args:
        question:             User's question about the paper
        paper_text:           Full extracted text of the paper
        conversation_history: Previous messages [{role, content}, ...]
        model:                Chat model (default: gpt-4o-mini)
        paper_title:          Paper title stored in Pinecone metadata
        paper_source:         Source e.g. arXiv, CORE, PMC

    Returns:
        Answer string, or None on empty result
    """
    if not question or not question.strip():
        raise ValueError("Empty question provided")

    if not paper_text or len(paper_text.strip()) < 100:
        raise ValueError("Paper text too short or empty for Q&A")

    try:
        if not (settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")):
            raise ValueError("OPENAI_API_KEY not configured")

        embeddings, llm = _get_models(model)
        pc = _get_pinecone()
        _ensure_index(pc)

        paper_id = _make_paper_id(paper_text)

        # _get_pinecone() already synced Settings/.env key into os.environ; pass explicitly too.
        vectorstore = PineconeVectorStore(
            index_name=INDEX_NAME,
            embedding=embeddings,
            namespace=paper_id,
            pinecone_api_key=os.environ["PINECONE_API_KEY"],
        )

        # Index only when needed — llm is now passed for contextual embeddings
        _index_paper(
            vectorstore=vectorstore,
            pc=pc,
            paper_text=paper_text,
            paper_id=paper_id,
            llm=llm,
            paper_title=paper_title,
            paper_source=paper_source,
        )

        # ── Retriever: Ensemble of BM25 (keyword) + Pinecone (semantic) ──────
        #
        # WHY: MMR + MultiQueryRetriever were the root cause of random failures.
        #   - MMR actively discards the most relevant chunk for "diversity"
        #   - MultiQueryRetriever generates noisy rephrased queries that can
        #     pull in off-topic chunks, pushing the right chunk out of top-k
        #
        # FIX: Hybrid retrieval — BM25 catches exact keyword matches that
        # semantic search misses (e.g. specific numbers, names, acronyms).
        # Pinecone semantic search catches meaning-based matches.
        # EnsembleRetriever fuses both with Reciprocal Rank Fusion (RRF),
        # which is far more stable than MMR for factual Q&A.

        # BM25 — keyword retrieval over raw (non-contextualized) chunks
        bm25_docs = _paper_chunks_cache.get(paper_id)
        if not bm25_docs:
            # Server restarted — rebuild BM25 from raw paper text (no LLM calls needed)
            logging.info(f"Rebuilding BM25 cache for paper {paper_id[:12]} after restart...")
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1200, chunk_overlap=200,
                separators=["\n\n", "\n", " ", ""],
            )
            meta = {"paper_id": paper_id}
            if paper_title:
                meta["paper_title"] = paper_title
            if paper_source:
                meta["paper_source"] = paper_source
            base_doc = Document(page_content=paper_text, metadata=meta)
            bm25_docs = splitter.split_documents([base_doc])
            for c in bm25_docs:
                c.metadata.update(meta)
            _paper_chunks_cache[paper_id] = bm25_docs

        bm25_retriever = BM25Retriever.from_documents(bm25_docs)
        bm25_retriever.k = 6

        # Pinecone — pure cosine similarity (NOT MMR) for consistent top-k ranking
        pinecone_retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 6},
        )

        # Ensemble — fuse both retrievers with equal weight using RRF
        retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, pinecone_retriever],
            weights=[0.4, 0.6],   # slightly favour semantic; tune if needed
        )

        # Determine if there is real conversation history
        chat_history_msgs = _to_langchain_messages(conversation_history)
        has_history = len(chat_history_msgs) > 0

        # Build chain — history-aware retriever only activated when needed
        rag_chain = _build_rag_chain(llm, retriever, has_history=has_history)

        result = rag_chain.invoke({
            "input": question.strip(),
            "chat_history": chat_history_msgs,
        })

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
    Same as ask_about_paper but loads/stores conversation_history under session_id
    (Upstash Redis when configured, otherwise in-memory per process).
    """
    if not session_id or not str(session_id).strip():
        raise ValueError("session_id is required")
    sid = str(session_id).strip()
    history = load_session(sid)
    answer = ask_about_paper(
        question=question,
        paper_text=paper_text,
        conversation_history=history if history else None,
        model=model,
        paper_title=paper_title,
        paper_source=paper_source,
    )
    if not answer:
        return None
    new_history = history + [
        {"role": "user", "content": question.strip()},
        {"role": "assistant", "content": answer},
    ]
    _save_session_messages(sid, new_history)
    return answer
