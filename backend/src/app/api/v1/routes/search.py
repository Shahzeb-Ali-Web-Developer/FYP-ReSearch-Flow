from fastapi import APIRouter, HTTPException, BackgroundTasks
from ....services.semantic_service import fetch_semantic_papers
from ....services.serpapi_service import fetch_google_papers_serpapi
from ....utils.dedupe import clean_and_deduplicate
from ....crud.papers_crud import store_to_supabase
import pandas as pd
import logging

router = APIRouter()

@router.get("/fetch")
def fetch_papers(topic: str, limit: int = 20, extract_content: bool = False):
    """
    Fetch research papers from Semantic Scholar and Google Scholar.
    
    - topic: Research topic to search
    - limit: Number of papers per source (default 20)
    - extract_content: Whether to download and extract PDF content (slow, default False)
    """
    try:
        logging.info(f"Starting fetch for topic: {topic}, limit: {limit}")
        
        # Fetch from Semantic Scholar
        semantic_df = fetch_semantic_papers(topic, limit=limit, extract_content=extract_content)
        logging.info(f"Semantic Scholar returned {len(semantic_df)} papers")
        
        # Fetch from Google Scholar
        google_df = fetch_google_papers_serpapi(topic, limit=limit, extract_content=extract_content)
        logging.info(f"Google Scholar returned {len(google_df)} papers")
        
        # Combine results
        if semantic_df.empty and google_df.empty:
            logging.warning(f"No papers found for topic: {topic}")
            return {
                "status": "no_results",
                "message": "No papers found for this topic",
                "count": 0,
                "semantic_count": 0,
                "google_count": 0
            }
        
        combined = pd.concat([semantic_df, google_df], ignore_index=True)
        logging.info(f"Combined total: {len(combined)} papers")
        
        # Clean and deduplicate
        cleaned = clean_and_deduplicate(combined, topic)
        logging.info(f"After cleaning: {len(cleaned)} papers")
        
        # Store to Supabase
        if not cleaned.empty:
            inserted = store_to_supabase(cleaned, topic)
            logging.info(f"Successfully stored {inserted} papers")
        else:
            inserted = 0
            logging.warning("No papers to store after cleaning")
        
        return {
            "status": "success",
            "count": inserted,
            "total_fetched": len(combined),
            "after_cleaning": len(cleaned),
            "semantic_count": len(semantic_df),
            "google_count": len(google_df)
        }
        
    except Exception as e:
        logging.error(f"Error in fetch_papers: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching papers: {str(e)}")