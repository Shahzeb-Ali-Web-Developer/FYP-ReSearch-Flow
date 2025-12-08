from fastapi import APIRouter, HTTPException, Body
from ....services.citation_network_service import build_citation_network_from_papers, build_citation_network
from typing import List, Optional
import logging

router = APIRouter()


@router.post("/network")
async def get_citation_network(
    request_data: dict = Body(...)
):
    """
    Build a citation network graph from paper IDs or paper objects.
    
    You can either:
    1. Provide paper_ids: List of OpenAlex work IDs
    2. Provide papers: List of paper dictionaries (from search results)
    
    The network will show how papers are connected through citations.
    """
    try:
        papers = request_data.get("papers", [])
        paper_ids = request_data.get("paper_ids", [])
        max_depth = request_data.get("max_depth", 1)
        max_nodes = request_data.get("max_nodes", 50)
        
        # Validate parameters
        if max_depth < 1 or max_depth > 2:
            max_depth = 1
        if max_nodes < 10 or max_nodes > 200:
            max_nodes = 50
        
        if papers and len(papers) > 0:
            # Build network from paper objects (more efficient)
            logging.info(f"Building citation network from {len(papers)} papers")
            network = build_citation_network_from_papers(papers, max_depth=max_depth, max_nodes=max_nodes)
        elif paper_ids and len(paper_ids) > 0:
            # Build network from paper IDs (requires API calls)
            logging.info(f"Building citation network from {len(paper_ids)} paper IDs")
            network = build_citation_network(paper_ids, max_depth=max_depth, max_nodes=max_nodes)
        else:
            raise HTTPException(
                status_code=400,
                detail="Either 'paper_ids' or 'papers' must be provided"
            )
        
        return {
            "status": "success",
            "network": network,
            "message": f"Citation network built with {network['stats']['totalNodes']} nodes and {network['stats']['totalEdges']} edges"
        }
        
    except Exception as e:
        logging.error(f"Error building citation network: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to build citation network",
                "message": str(e)
            }
        )
