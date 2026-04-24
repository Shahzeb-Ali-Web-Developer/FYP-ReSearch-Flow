"""
Semantic Scholar Search and Summarization Routes
"""
from fastapi import APIRouter, HTTPException, Body
from typing import Optional
import logging
from ....services.semantic_scholar_service import fetch_semantic_scholar_papers
from ....services.pdf_service import get_pdf_text_from_url
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




@router.post("/summarize")
async def summarize_paper_endpoint(
    request_data: dict = Body(...)
):
    """
    Summarize a research paper from any source (arXiv, CORE, PMC, etc.).
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
        
        if not pdf_url and not abstract:
            raise HTTPException(
                status_code=400,
                detail="'pdf_url' or 'abstract' must be provided"
            )
        
        pdf_text = None
        fallback_used = False
        
        # Try PDF extraction first
        if pdf_url:
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
            "pdf_text": "...(optional pre-extracted text)...",  # Skip PDF download if provided
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
        pdf_text_direct = request_data.get("pdf_text")  # Optional: pre-extracted text from frontend
        conversation_history = request_data.get("conversation_history", [])
        
        if not question or not question.strip():
            raise HTTPException(
                status_code=400,
                detail="Question is required"
            )
        
        logging.info(f"Question: {question[:100]}...")
        
        # --- OPTIMIZATION: Use pre-extracted text if provided by frontend ---
        # This avoids re-downloading and re-extracting the PDF on every question.
        if pdf_text_direct and len(pdf_text_direct.strip()) > 100:
            pdf_text = pdf_text_direct
            logging.info(f"Using pre-extracted PDF text ({len(pdf_text)} chars) — skipping PDF download")
        else:
            # Fall back to downloading and extracting from URL
            if not pdf_url:
                raise HTTPException(
                    status_code=400,
                    detail="Either 'pdf_url' or 'pdf_text' must be provided"
                )
            
            logging.info(f"Extracting PDF from URL: {pdf_url}")
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
        answer = ask_about_paper(
            question.strip(),
            pdf_text,
            conversation_history=conversation_history if conversation_history else None
        )
        
        return {
            "status": "success",
            "pdf_url": pdf_url or "(text provided directly)",
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


