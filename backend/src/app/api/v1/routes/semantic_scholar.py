"""
Semantic Scholar Search and Summarization Routes
"""
from fastapi import APIRouter, HTTPException, Body
from typing import Optional
import logging
from ....services.semantic_scholar_service import fetch_semantic_scholar_papers
from ....services.pdf_service import get_pdf_text_from_url, get_structured_pdf_text_from_url
from ....services.summarization_service import summarize_paper
from ....services.chat_service import ask_about_paper

router = APIRouter()


@router.get("/search")
async def search_semantic_scholar_papers(
    query: str,
    limit: int = 20
):
    """
    Search Semantic Scholar for papers matching the query.
    
    Args:
        query: Search query/topic
        limit: Maximum number of results (default: 20, max: 100)
    
    Returns:
        JSON response with list of papers
    """
    try:
        if not query or not query.strip():
            raise HTTPException(
                status_code=400,
                detail="Query parameter is required"
            )
        
        # Limit maximum results
        limit = min(limit, 100)
        
        logging.info(f"Searching Semantic Scholar for query: {query}, limit: {limit}")
        
        papers = fetch_semantic_scholar_papers(query.strip(), limit=limit)
        
        if not papers:
            return {
                "status": "no_results",
                "message": f"No papers found for query '{query}'",
                "count": 0,
                "papers": []
            }
        
        return {
            "status": "success",
            "message": f"Found {len(papers)} papers for '{query}'",
            "count": len(papers),
            "query": query,
            "papers": papers
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error searching Semantic Scholar: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to search Semantic Scholar",
                "message": str(e)
            }
        )


@router.post("/extract")
async def extract_pdf_content(
    request_data: dict = Body(...)
):
    """
    Extract full text content from a PDF (works with any source - arXiv, CORE, PMC, etc.).
    
    Request body:
        {
            "pdf_url": "https://example.com/paper.pdf"
        }
    
    Returns:
        Full extracted text from PDF
    """
    try:
        pdf_url = request_data.get("pdf_url")
        
        if not pdf_url:
            raise HTTPException(
                status_code=400,
                detail="'pdf_url' must be provided"
            )
        
        logging.info(f"Extracting PDF content from: {pdf_url}")
        
        # Extract full text from PDF (no page limit)
        pdf_text, extraction_error = get_pdf_text_from_url(pdf_url, max_pages=None)
        
        if pdf_text is None:
            error_message = extraction_error or "PDF is not available or could not be processed."
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "PDF not available",
                    "message": error_message
                }
            )
        
        return {
            "status": "success",
            "pdf_url": pdf_url,
            "full_text": pdf_text,
            "text_length": len(pdf_text),
            "character_count": len(pdf_text),
            "word_count": len(pdf_text.split())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error extracting PDF content: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to extract PDF content",
                "message": str(e)
            }
        )


@router.post("/extract-structured")
async def extract_structured_pdf_content(
    request_data: dict = Body(...)
):
    """
    Extract structured text content from a PDF with heading/subheading/body classification.
    Uses font size and style analysis to detect document structure.
    
    Request body:
        {
            "pdf_url": "https://example.com/paper.pdf"
        }
    
    Returns:
        Structured blocks with type classification
    """
    try:
        pdf_url = request_data.get("pdf_url")
        
        if not pdf_url:
            raise HTTPException(
                status_code=400,
                detail="'pdf_url' must be provided"
            )
        
        logging.info(f"Extracting structured PDF content from: {pdf_url}")
        
        structured_blocks, extraction_error = get_structured_pdf_text_from_url(pdf_url, max_pages=None)
        
        if structured_blocks is None:
            error_message = extraction_error or "PDF is not available or could not be processed."
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "PDF not available",
                    "message": error_message
                }
            )
        
        # Count block types for metadata
        heading_count = sum(1 for b in structured_blocks if b["type"] == "heading")
        subheading_count = sum(1 for b in structured_blocks if b["type"] == "subheading")
        body_count = sum(1 for b in structured_blocks if b["type"] == "body")
        total_chars = sum(len(b["text"]) for b in structured_blocks)
        
        return {
            "status": "success",
            "pdf_url": pdf_url,
            "blocks": structured_blocks,
            "block_count": len(structured_blocks),
            "heading_count": heading_count,
            "subheading_count": subheading_count,
            "body_count": body_count,
            "total_characters": total_chars
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error extracting structured PDF content: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to extract structured PDF content",
                "message": str(e)
            }
        )


@router.post("/summarize")
async def summarize_paper_endpoint(
    request_data: dict = Body(...)
):
    """
    Summarize a research paper from any source (arXiv, CORE, PMC, etc.).
    Works with any PDF URL regardless of original source.
    
    Request body:
        {
            "pdf_url": "https://example.com/paper.pdf"
        }
    
    Returns:
        Summary with problem_statement, methodology, key_findings, conclusion
    """
    try:
        pdf_url = request_data.get("pdf_url")
        
        if not pdf_url:
            raise HTTPException(
                status_code=400,
                detail="'pdf_url' must be provided"
            )
        
        logging.info(f"Summarizing paper from: {pdf_url}")
        
        # Extract text from PDF (full extraction - no page limit)
        pdf_text, extraction_error = get_pdf_text_from_url(pdf_url, max_pages=None)
        
        if pdf_text is None:
            error_message = extraction_error or "PDF is not available or could not be processed."
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "PDF not available",
                    "message": error_message
                }
            )
        
        # Generate summary using LLM (passes extracted content to LLM)
        logging.info(f"Generating summary for {len(pdf_text)} characters of text using LLM")
        summary = summarize_paper(pdf_text, max_sentences=5, use_llm=True)
        
        return {
            "status": "success",
            "pdf_url": pdf_url,
            "summary": summary,
            "full_text": pdf_text,  # Include full extracted text
            "text_length": len(pdf_text)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error summarizing paper: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to summarize paper",
                "message": str(e)
            }
        )


@router.post("/ask")
async def ask_question_endpoint(
    request_data: dict = Body(...)
):
    """
    Ask a question about a research paper from any source.
    Works with any PDF URL regardless of original source.
    
    Request body:
        {
            "pdf_url": "https://example.com/paper.pdf",
            "question": "What is the main contribution of this paper?",
            "conversation_history": [  # Optional
                {"role": "user", "content": "previous question"},
                {"role": "assistant", "content": "previous answer"}
            ]
        }
    
    Returns:
        Answer to the question
    """
    try:
        pdf_url = request_data.get("pdf_url")
        question = request_data.get("question")
        conversation_history = request_data.get("conversation_history", [])
        
        if not question or not question.strip():
            raise HTTPException(
                status_code=400,
                detail="Question is required"
            )
        
        if not pdf_url:
            raise HTTPException(
                status_code=400,
                detail="'pdf_url' must be provided"
            )
        
        logging.info(f"Question about paper from: {pdf_url}")
        logging.info(f"Question: {question[:100]}...")
        
        # Extract text from PDF (full extraction - no page limit)
        pdf_text, extraction_error = get_pdf_text_from_url(pdf_url, max_pages=None)
        
        if pdf_text is None:
            error_message = extraction_error or "PDF is not available or could not be processed."
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "PDF not available",
                    "message": error_message
                }
            )
        
        # Get answer from LLM
        answer = ask_about_paper(question.strip(), pdf_text, conversation_history=conversation_history if conversation_history else None)
        
        if not answer:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate answer. Please try again."
            )
        
        return {
            "status": "success",
            "pdf_url": pdf_url,
            "question": question,
            "answer": answer
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error answering question: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to answer question",
                "message": str(e)
            }
        )


