"""
PubMed Central (PMC) Search and Summarization Routes
"""
from fastapi import APIRouter, HTTPException, Body
from typing import Optional
import logging
from ....services.pmc_service import fetch_pmc_papers, get_pmc_fulltext_from_xml
from ....services.pdf_service import get_pdf_text_from_url
from ....services.summarization_service import summarize_paper
from ....services.llm_service import ask_question_with_llm

router = APIRouter()


@router.get("/search")
async def search_pmc_papers(
    query: str,
    limit: int = 20
):
    """
    Search PubMed Central for papers matching the query.
    
    Args:
        query: Search query/topic
        limit: Maximum number of results (default: 20, max: 10000)
    
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
        limit = min(limit, 10000)
        
        logging.info(f"Searching PMC for query: {query}, limit: {limit}")
        
        papers = fetch_pmc_papers(query.strip(), limit=limit)
        
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
        logging.error(f"Error searching PMC: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to search PMC",
                "message": str(e)
            }
        )


@router.post("/extract")
async def extract_pdf_content(
    request_data: dict = Body(...)
):
    """
    Extract full text content from a PMC PDF (no summarization).
    
    Request body:
        {
            "pdf_url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC123456/pdf/"
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
    Summarize a research paper from PMC.
    Falls back to abstract-based summarization if PDF is unavailable.
    
    Request body:
        {
            "pdf_url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC123456/pdf/",
            "pmc_id": "Optional PMC ID",
            "title": "Optional paper title for fallback",
            "abstract": "Optional abstract for fallback"
        }
    
    Returns:
        Summary with problem_statement, methodology, key_findings, conclusion
    """
    try:
        pdf_url = request_data.get("pdf_url")
        pmc_id = request_data.get("pmc_id")  # Optional: direct PMC ID
        title = request_data.get("title", "")
        abstract = request_data.get("abstract", "")
        pdf_text_direct = request_data.get("pdf_text")  # Optional: skip extraction
        
        if not pdf_url and not pmc_id and not abstract:
            raise HTTPException(
                status_code=400,
                detail="'pdf_url', 'pmc_id', or 'abstract' must be provided"
            )
        
        # Try to extract PMC ID from URL if not provided directly
        if not pmc_id and pdf_url:
            import re
            match = re.search(r'PMC(\d+)', pdf_url)
            if match:
                pmc_id = match.group(1)
        
        pdf_text = None
        extraction_error = None
        fallback_used = False

        # --- OPTIMIZATION: Use pre-extracted text if provided ---
        if pdf_text_direct and len(str(pdf_text_direct).strip()) > 100:
            pdf_text = str(pdf_text_direct)
            logging.info(f"Using pre-extracted PDF text ({len(pdf_text)} chars) — skipping PDF/XML download")
        
        # Strategy 1: Try PMC XML full-text API (no PDF download needed, bypasses interstitial)
        if pdf_text is None and pmc_id:
            logging.info(f"Trying PMC XML full-text extraction for PMC{pmc_id}")
            xml_text = get_pmc_fulltext_from_xml(pmc_id)
            if xml_text and len(xml_text.strip()) > 200:
                pdf_text = xml_text
                logging.info(f"Successfully got full-text from PMC XML: {len(pdf_text)} chars")
        
        # Strategy 2: Fall back to PDF download (uses Europe PMC direct link)
        if pdf_text is None and pdf_url:
            logging.info(f"XML extraction failed/unavailable, trying PDF download: {pdf_url}")
            pdf_text, extraction_error = get_pdf_text_from_url(pdf_url, max_pages=None)
        
        # Strategy 3: Fall back to abstract
        if pdf_text is None and abstract and len(abstract.strip()) > 50:
            logging.info(f"Using abstract-based fallback summarization for: {title[:80]}")
            fallback_text = ""
            if title:
                fallback_text += f"Title: {title}\n\n"
            fallback_text += f"Abstract: {abstract}"
            pdf_text = fallback_text
            fallback_used = True
        
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
            response["fallback_note"] = "Summary was generated from the paper's abstract because the full text could not be accessed directly."
            
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

@router.post("/ask")
async def ask_question_endpoint(
    request_data: dict = Body(...)
):
    """
    Ask a question about a research paper.
    """
    try:
        pdf_url = request_data.get("pdf_url")
        pmc_id = request_data.get("pmc_id")
        question = request_data.get("question")
        history = request_data.get("conversation_history", [])
        pdf_text_direct = request_data.get("pdf_text")
        
        if not question:
            raise HTTPException(status_code=400, detail="'question' must be provided")
            
        if not pmc_id and pdf_url:
            import re
            match = re.search(r'PMC(\d+)', pdf_url)
            if match:
                pmc_id = match.group(1)
            
        if not pdf_url and not pmc_id and not pdf_text_direct:
            raise HTTPException(
                status_code=400,
                detail="Either 'pdf_url', 'pmc_id', or 'pdf_text' must be provided"
            )
            
        pdf_text = None
        if pdf_text_direct and len(str(pdf_text_direct).strip()) > 100:
            pdf_text = str(pdf_text_direct)
            logging.info(f"Using pre-extracted PDF text ({len(pdf_text)} chars) for Q&A")
            
        if pdf_text is None and pmc_id:
            xml_text = get_pmc_fulltext_from_xml(pmc_id)
            if xml_text and len(xml_text.strip()) > 200:
                pdf_text = xml_text
                
        if pdf_text is None and pdf_url:
            pdf_text, extraction_error = get_pdf_text_from_url(pdf_url, max_pages=None)
            if pdf_text is None:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "PDF not available",
                        "message": extraction_error or "PDF could not be extracted"
                    }
                )
                
        if pdf_text is None:
            raise HTTPException(
                status_code=404,
                detail="PDF or XML content could not be extracted"
            )
                
        answer = ask_question_with_llm(pdf_text, question, history)
        
        if not answer:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate an answer from the paper content"
            )
            
        return {
            "status": "success",
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
