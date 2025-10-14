from fastapi import APIRouter, HTTPException, BackgroundTasks
from ....services.semantic_service import fetch_semantic_papers
from ....services.serpapi_service import fetch_google_papers_serpapi
from ....utils.dedupe import clean_and_deduplicate
from ....crud.papers_crud import store_to_supabase
import pandas as pd
import logging

router = APIRouter()

def store_papers_background(cleaned_df, topic):
    """Background task to store papers in Supabase"""
    try:
        if not cleaned_df.empty:
            inserted = store_to_supabase(cleaned_df, topic)
            logging.info(f"Background: Stored {inserted} papers for '{topic}'")
    except Exception as e:
        logging.error(f"Background storage error: {str(e)}")

@router.get("/fetch")
def fetch_papers(
    topic: str, 
    limit: int = 20, 
    extract_content: bool = False,
    background_tasks: BackgroundTasks = None
):
    """
    Fetch research papers and return immediately while storing in background.
    Returns papers in format ready for frontend display.
    """
    try:
        logging.info(f"Fetching papers for: {topic}")
        
        # Fetch from both sources
        semantic_df = fetch_semantic_papers(topic, limit=limit, extract_content=extract_content)
        logging.info(f"Semantic Scholar: {len(semantic_df)} papers")
        
        google_df = fetch_google_papers_serpapi(topic, limit=limit, extract_content=extract_content)
        logging.info(f"Google Scholar: {len(google_df)} papers")
        
        # Check if no results
        if semantic_df.empty and google_df.empty:
            logging.warning(f"No results for: {topic}")
            return {
                "status": "no_results",
                "message": f"No papers found for '{topic}'. Try different keywords.",
                "count": 0,
                "papers": []
            }
        
        # Combine and clean
        combined = pd.concat([semantic_df, google_df], ignore_index=True)
        cleaned = clean_and_deduplicate(combined, topic)
        
        # Convert to list of dicts for JSON
        papers_list = cleaned.to_dict('records')
        
        # Store in background (non-blocking)
        if background_tasks and not cleaned.empty:
            background_tasks.add_task(store_papers_background, cleaned, topic)
            logging.info(f"Queued {len(cleaned)} papers for background storage")
        
        # Return formatted response
        return {
            "status": "success",
            "message": f"Found {len(papers_list)} papers for '{topic}'",
            "count": len(papers_list),
            "topic": topic,
            "papers": papers_list,
            "sources": {
                "semantic_scholar": len(semantic_df),
                "google_scholar": len(google_df)
            }
        }
        
    except Exception as e:
        logging.error(f"Error fetching papers: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "Failed to fetch papers",
                "message": str(e)
            }
        )