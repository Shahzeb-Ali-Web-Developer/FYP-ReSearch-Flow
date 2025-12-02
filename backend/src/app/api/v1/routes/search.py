from fastapi import APIRouter, HTTPException, BackgroundTasks
from ....services.openalex_service import fetch_openalex_papers
from ....utils.dedupe import clean_and_deduplicate
from ....crud.papers_crud import store_to_supabase
import logging
import asyncio

router = APIRouter()

async def store_papers_background(cleaned_df, topic):
    """Background task to store papers in Supabase"""
    try:
        if not cleaned_df.empty:
            # Run in executor to prevent blocking
            loop = asyncio.get_event_loop()
            inserted = await loop.run_in_executor(
                None, 
                store_to_supabase, 
                cleaned_df, 
                topic
            )
            logging.info(f"Background storage complete: {inserted} papers for '{topic}'")
            print(f"✓ Background storage complete: {inserted} papers saved to database")
    except Exception as e:
        logging.error(f"Background storage error: {str(e)}")
        print(f"✗ Background storage error: {str(e)}")

@router.get("/fetch")
async def fetch_papers(
    topic: str, 
    limit: int = 20, 
    extract_content: bool = False,
    background_tasks: BackgroundTasks = None
):
    """
    Fetch research papers from OpenAlex and return immediately while
    optionally storing them in Supabase in the background.
    """
    try:
        logging.info(f"Starting fetch for topic: {topic}, limit: {limit}")
        
        # Fetch from OpenAlex
        openalex_df = fetch_openalex_papers(topic, limit=limit)
        logging.info(f"OpenAlex: {len(openalex_df)} papers")
        
        # Check if no results
        if openalex_df.empty:
            logging.warning(f"No results for: {topic}")
            return {
                "status": "no_results",
                "message": f"No papers found for '{topic}'. Try different keywords.",
                "count": 0,
                "papers": []
            }

        # Clean (normalization + basic dedupe by title)
        cleaned = clean_and_deduplicate(openalex_df, topic)
        
        # Convert to list of dicts for JSON
        papers_list = cleaned.to_dict('records')
        
        # Store in background (non-blocking)
        if background_tasks and not cleaned.empty:
            background_tasks.add_task(store_papers_background, cleaned, topic)
            logging.info(f"✓ Queued {len(cleaned)} papers for background storage")
            print(f"✓ Returning {len(papers_list)} papers to user, saving to DB in background...")
        
        # Return formatted response immediately
        return {
            "status": "success",
            "message": f"Found {len(papers_list)} papers for '{topic}'",
            "count": len(papers_list),
            "topic": topic,
            "papers": papers_list,
            "sources": {
                "openalex": len(openalex_df),
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