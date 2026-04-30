"""
CORE Search and Summarization Routes
"""
from fastapi import APIRouter, HTTPException, Body
from typing import Optional
import logging
from ....services.core_service import fetch_core_papers
from ....services.pdf_service import get_pdf_text_from_url
from ....services.summarization_service import summarize_paper

router = APIRouter()


@router.get("/search")
async def search_core_papers(
    query: str,
    limit: int = 20
):
    """
    Search CORE for papers matching the query.
    
    Args:
        query: Search query/topic
        limit: Maximum number of results (default: 20, max: 500)
    
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
        limit = min(limit, 500)
        
        logging.info(f"Searching CORE for query: {query}, limit: {limit}")
        
        papers = fetch_core_papers(query.strip(), limit=limit)
        
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
        logging.error(f"Error searching CORE: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to search CORE",
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


@router.post("/summarize")
async def summarize_paper_endpoint(
    request_data: dict = Body(...)
):
    """
    Summarize a research paper from CORE.
    Works with any PDF URL regardless of original source.
    Falls back to abstract-based summarization if PDF is unavailable.
    
    Request body:
        {
            "pdf_url": "https://example.com/paper.pdf",
            "title": "Optional paper title for fallback",
            "abstract": "Optional abstract for fallback"
        }
    
    Returns:
        Summary with problem_statement, methodology, key_findings, conclusion
    """
    try:
        pdf_url = request_data.get("pdf_url")
        title = request_data.get("title", "")
        abstract = request_data.get("abstract", "")
        pdf_text_direct = request_data.get("pdf_text")  # Optional: skip extraction
        
        if not pdf_url and not abstract:
            raise HTTPException(
                status_code=400,
                detail="'pdf_url' or 'abstract' must be provided"
            )
        
        pdf_text = None
        fallback_used = False

        # --- OPTIMIZATION: Use pre-extracted text if provided ---
        if pdf_text_direct and len(str(pdf_text_direct).strip()) > 100:
            pdf_text = str(pdf_text_direct)
            logging.info(f"Using pre-extracted PDF text ({len(pdf_text)} chars) — skipping PDF download")
        
        # Try PDF extraction first
        if pdf_text is None and pdf_url:
            logging.info(f"Summarizing paper from: {pdf_url}")
            pdf_text, extraction_error = get_pdf_text_from_url(pdf_url, max_pages=None)
            
            if pdf_text is None:
                logging.warning(f"PDF extraction failed: {extraction_error}")
        
        # Fallback: use abstract if PDF extraction failed
        if pdf_text is None and abstract and len(abstract.strip()) > 50:
            logging.info(f"Using abstract-based fallback summarization for: {title[:80]}")
            fallback_text = ""
            if title:
                fallback_text += f"Title: {title}\n\n"
            fallback_text += f"Abstract: {abstract}"
            pdf_text = fallback_text
            fallback_used = True
        
        if pdf_text is None:
            error_message = "PDF is not available and no abstract was provided for fallback summarization."
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "PDF not available",
                    "message": error_message
                }
            )
        
        # Generate summary using LLM (passes extracted content to LLM)
        logging.info(f"Generating summary for {len(pdf_text)} characters of text using LLM (fallback={fallback_used})")
        summary = summarize_paper(pdf_text, max_sentences=5, use_llm=True)
        
        response = {
            "status": "success",
            "pdf_url": pdf_url,
            "summary": summary,
            "full_text": pdf_text if not fallback_used else None,
            "text_length": len(pdf_text)
        }
        
        if fallback_used:
            response["fallback"] = True
            response["fallback_note"] = "Summary was generated from the paper's abstract because the PDF could not be accessed directly."
        
        return response
        
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
