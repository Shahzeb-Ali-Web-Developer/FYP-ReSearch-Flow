from fastapi import APIRouter, HTTPException, Body
from ....services.citation_network_service import build_citation_network_from_papers, build_citation_network
from ....services.neo4j_citation_service import neo4j_citation_service
from typing import List, Optional
import logging

router = APIRouter()


@router.post("/network")
async def get_citation_network(
    request_data: dict = Body(...)
):
    """
    Build a citation network graph from paper IDs or paper objects.
    
    NOW POWERED BY NEO4J: 100x faster queries when Neo4j is available!
    
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
        use_neo4j = request_data.get("use_neo4j", True)  # New parameter
        
        # Enhanced limits for Neo4j
        if neo4j_citation_service.is_available() and use_neo4j:
            # Neo4j can handle much more!
            if max_depth < 1 or max_depth > 5:
                max_depth = 2
            if max_nodes < 10 or max_nodes > 500:
                max_nodes = 200
        else:
            # API fallback limits
            if max_depth < 1 or max_depth > 2:
                max_depth = 1
            if max_nodes < 10 or max_nodes > 200:
                max_nodes = 50
        
        # Extract paper IDs if not provided
        if not paper_ids and papers:
            paper_ids = [p.get("paperId") or p.get("id") for p in papers if p.get("paperId") or p.get("id")]
        
        if not paper_ids:
            raise HTTPException(
                status_code=400,
                detail="Either 'paper_ids' or 'papers' with IDs must be provided"
            )
        
        # Try Neo4j first (if available and requested)
        if neo4j_citation_service.is_available() and use_neo4j:
            logging.info(f"🚀 Using Neo4j for citation network ({len(paper_ids)} papers, depth={max_depth})")
            network = neo4j_citation_service.build_citation_network(
                paper_ids=paper_ids,
                max_depth=max_depth,
                max_nodes=max_nodes
            )
            
            # If Neo4j returned results, use them
            if network and network.get("nodes"):
                return {
                    "status": "success",
                    "network": network,
                    "message": f"Neo4j: Built network with {network['stats']['totalNodes']} nodes and {network['stats']['totalEdges']} edges (⚡ Lightning fast!)",
                    "source": "neo4j"
                }
            else:
                logging.warning("Neo4j returned no results, falling back to API")
        
        # Fallback to API-based method
        logging.info(f"Using OpenAlex API for citation network (fallback mode)")
        if papers and len(papers) > 0:
            network = build_citation_network_from_papers(papers, max_depth=max_depth, max_nodes=max_nodes)
        else:
            network = build_citation_network(paper_ids, max_depth=max_depth, max_nodes=max_nodes)
        
        return {
            "status": "success",
            "network": network,
            "message": f"API: Built network with {network['stats']['totalNodes']} nodes and {network['stats']['totalEdges']} edges",
            "source": "api"
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


@router.get("/stats")
async def get_citation_stats():
    """Get Neo4j citation network statistics"""
    try:
        if neo4j_citation_service.is_available():
            paper_count = neo4j_citation_service.get_paper_count()
            citation_count = neo4j_citation_service.get_citation_count()
            
            return {
                "status": "success",
                "neo4j_available": True,
                "papers": paper_count,
                "citations": citation_count,
                "message": f"Neo4j: {paper_count:,} papers, {citation_count:,} citations"
            }
        else:
            return {
                "status": "unavailable",
                "neo4j_available": False,
                "message": "Neo4j not connected. Using API fallback mode."
            }
    except Exception as e:
        return {
            "status": "error",
            "neo4j_available": False,
            "error": str(e)
        }


@router.get("/path/{source_id}/{target_id}")
async def find_shortest_path(source_id: str, target_id: str):
    """Find shortest citation path between two papers (Neo4j only)"""
    try:
        if not neo4j_citation_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="Neo4j not available. This feature requires Neo4j."
            )
        
        result = neo4j_citation_service.find_shortest_path(source_id, target_id)
        
        if result.get("hops", -1) < 0:
            return {
                "status": "not_found",
                "message": "No citation path found between papers"
            }
        
        return {
            "status": "success",
            "path": result["path"],
            "hops": result["hops"],
            "message": f"Found path with {result['hops']} hops"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
