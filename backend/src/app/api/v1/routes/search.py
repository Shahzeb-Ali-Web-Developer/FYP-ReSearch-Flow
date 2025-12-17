from fastapi import APIRouter, HTTPException, BackgroundTasks
from ....services.openalex_service import fetch_openalex_papers
from ....services.neo4j_citation_service import neo4j_citation_service
from ....utils.dedupe import clean_and_deduplicate
from ....crud.papers_crud import store_to_supabase
import logging
import asyncio

router = APIRouter()

async def store_papers_background(cleaned_df, topic):
    """Background task to store papers in Supabase AND Neo4j"""
    try:
        if not cleaned_df.empty:
            # Store in Supabase
            loop = asyncio.get_event_loop()
            inserted = await loop.run_in_executor(
                None, 
                store_to_supabase, 
                cleaned_df, 
                topic
            )
            logging.info(f"Supabase: Stored {inserted} papers for '{topic}'")
            print(f"[OK] Supabase: {inserted} papers saved")
            
            # Also store in Neo4j (if available)
            if neo4j_citation_service.is_available():
                try:
                    papers_list = cleaned_df.to_dict('records')
                    neo4j_stored = 0
                    citations_stored = 0
                    
                    # Store papers
                    for paper in papers_list:
                        if neo4j_citation_service.store_paper(paper):
                            neo4j_stored += 1
                    
                    # Store citations
                    citations = []
                    for paper in papers_list:
                        paper_id = paper.get("paperid") or paper.get("paperId")
                        refs = paper.get("referencedworks", []) or []
                        if isinstance(refs, list):
                            for ref_id in refs[:50]:  # Limit per paper
                                if ref_id:
                                    citations.append((paper_id, ref_id))
                    
                    if citations:
                        citations_stored = neo4j_citation_service.bulk_store_citations(citations)
                    
                    logging.info(f"Neo4j: Stored {neo4j_stored} papers, {citations_stored} citations")
                    print(f"[OK] Neo4j: {neo4j_stored} papers, {citations_stored} citations saved")
                    
                except Exception as neo4j_error:
                    logging.warning(f"Neo4j storage error (non-critical): {neo4j_error}")
                    print(f"[WARN] Neo4j storage skipped: {neo4j_error}")
                    
    except Exception as e:
        logging.error(f"Background storage error: {str(e)}")
        print(f"[ERROR] Background storage error: {str(e)}")

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
            logging.info(f"[OK] Queued {len(cleaned)} papers for background storage")
            print(f"[OK] Returning {len(papers_list)} papers to user, saving to DB in background...")
        
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