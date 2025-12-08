import logging
from typing import List, Dict, Any, Set, Tuple, Optional
import requests
from collections import defaultdict

OPENALEX_BASE_URL = "https://api.openalex.org"


def fetch_work_details(work_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch detailed information about a specific work from OpenAlex.
    """
    try:
        # Extract OpenAlex ID if it's a full URL
        if work_id.startswith("https://openalex.org/"):
            work_id = work_id.replace("https://openalex.org/", "")
        
        url = f"{OPENALEX_BASE_URL}/works/{work_id}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logging.warning(f"Failed to fetch work {work_id}: {str(e)}")
        return None


def build_citation_network(paper_ids: List[str], max_depth: int = 1, max_nodes: int = 50) -> Dict[str, Any]:
    """
    Build a citation network graph from a list of paper IDs.
    
    Args:
        paper_ids: List of OpenAlex work IDs to build network from
        max_depth: How many levels of citations to explore (1 = direct citations only)
        max_nodes: Maximum number of nodes in the graph
    
    Returns:
        Dictionary with 'nodes' and 'edges' for the citation graph
    """
    logging.info(f"Building citation network for {len(paper_ids)} papers, max_depth={max_depth}, max_nodes={max_nodes}")
    
    nodes: Dict[str, Dict[str, Any]] = {}  # paper_id -> node data
    edges: List[Dict[str, Any]] = []  # List of edge objects
    visited: Set[str] = set()
    to_process: List[Tuple[str, int]] = [(pid, 0) for pid in paper_ids]  # (paper_id, depth)
    
    # Fetch initial papers
    for paper_id in paper_ids:
        if paper_id in visited or len(nodes) >= max_nodes:
            continue
            
        work = fetch_work_details(paper_id)
        if work:
            visited.add(paper_id)
            nodes[paper_id] = {
                "id": paper_id,
                "label": work.get("display_name", "Unknown Title")[:100],  # Truncate long titles
                "title": work.get("display_name", "Unknown Title"),
                "year": work.get("publication_year"),
                "citationCount": work.get("cited_by_count", 0),
                "authors": [
                    (a.get("author") or {}).get("display_name", "Unknown")
                    for a in (work.get("authorships") or [])[:3]  # First 3 authors
                ],
                "venue": (work.get("primary_location") or {}).get("source", {}).get("display_name", "N/A"),
                "isRoot": True  # Mark initial papers
            }
    
    # Build network by following citations
    while to_process and len(nodes) < max_nodes:
        current_id, depth = to_process.pop(0)
        
        if depth >= max_depth:
            continue
            
        work = fetch_work_details(current_id)
        if not work:
            continue
        
        # Get papers this work references (outgoing citations)
        referenced_works = work.get("referenced_works", [])[:10]  # Limit to first 10
        
        for ref_id in referenced_works:
            if len(nodes) >= max_nodes:
                break
                
            # Add edge from current to referenced paper
            if current_id in nodes:
                edges.append({
                    "source": current_id,
                    "target": ref_id,
                    "type": "cites"
                })
            
            # Add referenced paper as node if not already added
            if ref_id not in visited and ref_id not in nodes:
                ref_work = fetch_work_details(ref_id)
                if ref_work:
                    visited.add(ref_id)
                    nodes[ref_id] = {
                        "id": ref_id,
                        "label": ref_work.get("display_name", "Unknown Title")[:100],
                        "title": ref_work.get("display_name", "Unknown Title"),
                        "year": ref_work.get("publication_year"),
                        "citationCount": ref_work.get("cited_by_count", 0),
                        "authors": [
                            (a.get("author") or {}).get("display_name", "Unknown")
                            for a in (ref_work.get("authorships") or [])[:3]
                        ],
                        "venue": (ref_work.get("primary_location") or {}).get("source", {}).get("display_name", "N/A"),
                        "isRoot": False
                    }
                    to_process.append((ref_id, depth + 1))
    
    # Filter edges to only include nodes we have
    valid_node_ids = set(nodes.keys())
    edges = [e for e in edges if e["source"] in valid_node_ids and e["target"] in valid_node_ids]
    
    # Convert nodes dict to list
    nodes_list = list(nodes.values())
    
    logging.info(f"Citation network built: {len(nodes_list)} nodes, {len(edges)} edges")
    
    return {
        "nodes": nodes_list,
        "edges": edges,
        "stats": {
            "totalNodes": len(nodes_list),
            "totalEdges": len(edges),
            "rootNodes": sum(1 for n in nodes_list if n.get("isRoot", False))
        }
    }


def build_citation_network_from_papers(papers: List[Dict[str, Any]], max_depth: int = 1, max_nodes: int = 50) -> Dict[str, Any]:
    """
    Build citation network from a list of paper dictionaries (from search results).
    This is more efficient as it uses existing paper data.
    """
    logging.info(f"Building citation network from {len(papers)} papers")
    
    nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []
    visited: Set[str] = set()
    
    # Add initial papers as nodes
    for paper in papers:
        paper_id = paper.get("paperId") or paper.get("id")
        if not paper_id or paper_id in visited:
            continue
            
        visited.add(paper_id)
        nodes[paper_id] = {
            "id": paper_id,
            "label": (paper.get("title") or "Unknown Title")[:100],
            "title": paper.get("title", "Unknown Title"),
            "year": paper.get("year"),
            "citationCount": paper.get("citationCount", 0),
            "authors": paper.get("authors", [])[:3],
            "venue": paper.get("venue", "N/A"),
            "isRoot": True
        }
        
        # Add edges for referenced works that are in our paper set
        referenced_works = paper.get("referencedWorks", []) or []
        for ref_id in referenced_works:
            # Check if referenced paper is in our current set
            ref_paper = next((p for p in papers if (p.get("paperId") or p.get("id")) == ref_id), None)
            
            if ref_paper:
                ref_paper_id = ref_paper.get("paperId") or ref_paper.get("id")
                if ref_paper_id not in nodes:
                    nodes[ref_paper_id] = {
                        "id": ref_paper_id,
                        "label": (ref_paper.get("title") or "Unknown Title")[:100],
                        "title": ref_paper.get("title", "Unknown Title"),
                        "year": ref_paper.get("year"),
                        "citationCount": ref_paper.get("citationCount", 0),
                        "authors": ref_paper.get("authors", [])[:3],
                        "venue": ref_paper.get("venue", "N/A"),
                        "isRoot": True
                    }
                
                edges.append({
                    "source": paper_id,
                    "target": ref_paper_id,
                    "type": "cites"
                })
    
    # Filter edges to only include nodes we have
    valid_node_ids = set(nodes.keys())
    edges = [e for e in edges if e["source"] in valid_node_ids and e["target"] in valid_node_ids]
    
    nodes_list = list(nodes.values())
    
    logging.info(f"Citation network built: {len(nodes_list)} nodes, {len(edges)} edges")
    
    return {
        "nodes": nodes_list,
        "edges": edges,
        "stats": {
            "totalNodes": len(nodes_list),
            "totalEdges": len(edges),
            "rootNodes": sum(1 for n in nodes_list if n.get("isRoot", False))
        }
    }
