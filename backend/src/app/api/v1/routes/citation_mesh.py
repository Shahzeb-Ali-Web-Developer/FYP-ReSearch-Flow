from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
from ....db.client_supabase import supabase

router = APIRouter()

@router.get("/graph")
async def get_citation_graph(topic: str = None, paper_ids: str = None):
    """
    Build a citation graph from papers.
    
    Args:
        topic: Filter papers by topic (optional)
        paper_ids: Comma-separated list of paper IDs to include (optional)
    
    Returns:
        Graph structure with nodes (papers) and edges (citations)
    """
    try:
        # Fetch papers from database
        query = supabase.table("research_papers").select("*")
        
        if topic:
            query = query.eq("topic", topic.lower().strip())
        
        if paper_ids:
            paper_id_list = [pid.strip() for pid in paper_ids.split(",")]
            query = query.in_("paperid", paper_id_list)
        
        # Limit to reasonable number for visualization
        query = query.limit(100)
        
        response = query.execute()
        papers = response.data
        
        if not papers:
            return {
                "nodes": [],
                "edges": [],
                "message": "No papers found"
            }
        
        # Build node map: paperId -> paper data
        node_map: Dict[str, Dict[str, Any]] = {}
        edge_list: List[Dict[str, str]] = []
        
        # Create nodes from papers
        for paper in papers:
            paper_id = paper.get("paperid")
            if not paper_id:
                continue
                
            node_map[paper_id] = {
                "id": paper_id,
                "title": paper.get("title", "Untitled"),
                "year": paper.get("year"),
                "citationCount": paper.get("citationcount", 0),
                "authors": paper.get("authors", [])[:3],  # First 3 authors
                "venue": paper.get("venue"),
                "isOpenAccess": paper.get("isopenaccess", False)
            }
        
        # Build edges from referencedWorks
        for paper in papers:
            paper_id = paper.get("paperid")
            referenced_works = paper.get("referencedworks", [])
            
            if not paper_id or not referenced_works:
                continue
            
            # Handle both JSON string and list formats
            if isinstance(referenced_works, str):
                try:
                    import json
                    referenced_works = json.loads(referenced_works)
                except:
                    referenced_works = []
            
            if not isinstance(referenced_works, list):
                continue
            
            # Create edges for each reference
            for ref_id in referenced_works:
                # Only include edges if both papers are in our dataset
                if ref_id in node_map:
                    edge_list.append({
                        "source": paper_id,
                        "target": ref_id,
                        "type": "cites"  # This paper cites the referenced paper
                    })
        
        # Convert node_map to list
        nodes = list(node_map.values())
        
        # Remove duplicate edges
        seen_edges = set()
        unique_edges = []
        for edge in edge_list:
            edge_key = (edge["source"], edge["target"])
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                unique_edges.append(edge)
        
        logging.info(f"Citation graph: {len(nodes)} nodes, {len(unique_edges)} edges")
        
        return {
            "nodes": nodes,
            "edges": unique_edges,
            "stats": {
                "nodeCount": len(nodes),
                "edgeCount": len(unique_edges),
                "topic": topic
            }
        }
        
    except Exception as e:
        logging.error(f"Error building citation graph: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to build citation graph",
                "message": str(e)
            }
        )
