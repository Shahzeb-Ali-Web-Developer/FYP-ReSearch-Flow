"""
arXiv Search and Summarization Routes
"""
from fastapi import APIRouter, HTTPException, Body
from typing import Optional
import logging
from ....services.arxiv_service import fetch_arxiv_papers
from ....services.pdf_service import get_pdf_text_from_url
from ....services.summarization_service import summarize_paper
from ....services.chat_service import ask_about_paper

router = APIRouter()


@router.get("/search")
async def search_arxiv_papers(
    query: str,
    limit: int = 20
):
    """
    Search arXiv for papers matching the query.
    
    Args:
        query: Search query/topic
        limit: Maximum number of results (default: 20, max: 2000)
    
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
        limit = min(limit, 2000)
        
        logging.info(f"Searching arXiv for query: {query}, limit: {limit}")
        
        papers = fetch_arxiv_papers(query.strip(), limit=limit)
        
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
        logging.error(f"Error searching arXiv: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to search arXiv",
                "message": str(e)
            }
        )


@router.post("/extract")
async def extract_pdf_content(
    request_data: dict = Body(...)
):
    """
    Extract full text content from a PDF (no summarization).
    
    Request body:
        {
            "arxiv_id": "1234.5678" OR "pdf_url": "https://arxiv.org/pdf/1234.5678.pdf"
        }
    
    Returns:
        Full extracted text from PDF
    """
    try:
        arxiv_id = request_data.get("arxiv_id")
        pdf_url = request_data.get("pdf_url")
        
        if not arxiv_id and not pdf_url:
            raise HTTPException(
                status_code=400,
                detail="Either 'arxiv_id' or 'pdf_url' must be provided"
            )
        
        # Construct PDF URL if arXiv ID is provided
        if arxiv_id:
            clean_id = arxiv_id.split('v')[0] if 'v' in arxiv_id else arxiv_id
            pdf_url = f"https://arxiv.org/pdf/{clean_id}.pdf"
        
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
            "arxiv_id": arxiv_id or pdf_url.split('/')[-1].replace('.pdf', ''),
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


@router.post("/summarize")
async def summarize_paper_endpoint(
    request_data: dict = Body(...)
):
    """
    Summarize a research paper from arXiv.
    
    Request body:
        {
            "arxiv_id": "1234.5678" OR "pdf_url": "https://arxiv.org/pdf/1234.5678.pdf"
        }
    
    Returns:
        Summary with problem_statement, methodology, key_findings, conclusion
    """
    try:
        arxiv_id = request_data.get("arxiv_id")
        pdf_url = request_data.get("pdf_url")
        
        if not arxiv_id and not pdf_url:
            raise HTTPException(
                status_code=400,
                detail="Either 'arxiv_id' or 'pdf_url' must be provided"
            )
        
        # Construct PDF URL if arXiv ID is provided
        if arxiv_id:
            # Handle version numbers (e.g., "1234.5678v1" -> "1234.5678")
            clean_id = arxiv_id.split('v')[0] if 'v' in arxiv_id else arxiv_id
            pdf_url = f"https://arxiv.org/pdf/{clean_id}.pdf"
        
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
            "arxiv_id": arxiv_id or pdf_url.split('/')[-1].replace('.pdf', ''),
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
    Ask a question about a research paper.
    
    Request body:
        {
            "arxiv_id": "1234.5678" OR "pdf_url": "...",
            "question": "What is the main contribution of this paper?",
            "pdf_text": "...(optional pre-extracted text)...",
            "conversation_history": []  # Optional
        }
    """
    try:
        arxiv_id = request_data.get("arxiv_id")
        pdf_url = request_data.get("pdf_url")
        question = request_data.get("question")
        pdf_text_direct = request_data.get("pdf_text")  # Optional: skip extraction
        conversation_history = request_data.get("conversation_history", [])
        
        if not question or not question.strip():
            raise HTTPException(status_code=400, detail="Question is required")
        
        logging.info(f"Question: {question[:100]}...")
        
        # --- OPTIMIZATION: Use pre-extracted text if provided ---
        if pdf_text_direct and len(pdf_text_direct.strip()) > 100:
            pdf_text = pdf_text_direct
            logging.info(f"Using pre-extracted PDF text ({len(pdf_text)} chars) — skipping PDF download")
        else:
            if not arxiv_id and not pdf_url:
                raise HTTPException(
                    status_code=400,
                    detail="Either 'arxiv_id', 'pdf_url', or 'pdf_text' must be provided"
                )
            if arxiv_id:
                clean_id = arxiv_id.split('v')[0] if 'v' in arxiv_id else arxiv_id
                pdf_url = f"https://arxiv.org/pdf/{clean_id}.pdf"
            
            logging.info(f"Extracting PDF from URL: {pdf_url}")
            pdf_text, extraction_error = get_pdf_text_from_url(pdf_url, max_pages=None)
            
            if pdf_text is None:
                error_message = extraction_error or "PDF is not available or could not be processed."
                raise HTTPException(
                    status_code=404,
                    detail={"error": "PDF not available", "message": error_message}
                )
        
        answer = ask_about_paper(
            question.strip(),
            pdf_text,
            conversation_history=conversation_history if conversation_history else None
        )
        
        if not answer:
            raise HTTPException(status_code=500, detail="Failed to generate answer. Please try again.")
        
        return {
            "status": "success",
            "arxiv_id": arxiv_id or (pdf_url.split('/')[-1].replace('.pdf', '') if pdf_url else None),
            "question": question,
            "answer": answer
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error answering question: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to answer question", "message": str(e)}
        )

