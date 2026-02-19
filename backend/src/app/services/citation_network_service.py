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
                "venue": ((work.get("primary_location") or {}).get("source") or {}).get("display_name", "N/A"),
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
                        "venue": ((ref_work.get("primary_location") or {}).get("source") or {}).get("display_name", "N/A"),
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
    Build an interconnected citation network from search results (optimized for speed).
    
    Strategy:
    1. Start with root papers (search results)
    2. Fetch papers they cite (1 level deep)
    3. Find connections between papers
    4. Create a useful, interconnected graph quickly
    """
    logging.info(f"Building citation network from {len(papers)} papers, max_depth={max_depth}, max_nodes={max_nodes}")
    
    nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []
    visited: Set[str] = set()
    root_ids: Set[str] = set()
    to_process: List[Tuple[str, int, str]] = []  # (paper_id, depth, relation_type)
    
    # Step 1: Add root papers (search results)
    for paper in papers:
        paper_id = paper.get("paperId") or paper.get("id")
        if not paper_id or paper_id in visited:
            continue
            
        visited.add(paper_id)
        root_ids.add(paper_id)
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
        to_process.append((paper_id, 0, "root"))
    
    # Step 2: Build comprehensive network by exploring citations
    while to_process and len(nodes) < max_nodes:
        current_id, depth, relation = to_process.pop(0)
        
        if depth >= max_depth:
            continue
        
        work = fetch_work_details(current_id)
        if not work:
            continue
        
        # Get papers this work CITES (forward citations - references)
        referenced_works = work.get("referenced_works", [])[:10]  # Limit for speed
        
        for ref_id in referenced_works:
            if len(nodes) >= max_nodes:
                break
            
            # Normalize ID
            if ref_id.startswith("https://openalex.org/"):
                ref_id = ref_id.replace("https://openalex.org/", "")
            
            # Add edge
            if current_id in nodes:
                edges.append({
                    "source": current_id,
                    "target": ref_id,
                    "type": "cites"
                })
            
            # Add node if not already added
            if ref_id not in visited:
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
                        "venue": ((ref_work.get("primary_location") or {}).get("source") or {}).get("display_name", "N/A"),
                        "isRoot": False
                    }
                    # Continue exploring from this paper (go deeper) - but only 1 level
                    if depth < max_depth - 1:
                        to_process.append((ref_id, depth + 1, "reference"))
    
    # Step 3: Find additional connections between existing nodes (quick check)
    # Check if any of our nodes cite each other (cross-references)
    node_ids = list(nodes.keys())
    connection_count = len(edges)
    
    if connection_count < len(node_ids) * 0.2:  # If graph is very sparse, find more connections
        logging.info("Finding additional cross-references...")
        for node_id in node_ids[:10]:  # Check first 10 nodes only
            if len(edges) >= max_nodes:  # Stop if we have enough edges
                break
            
            work = fetch_work_details(node_id)
            if work:
                refs = work.get("referenced_works", [])[:15]
                for ref in refs:
                    ref_clean = ref.replace("https://openalex.org/", "")
                    if ref_clean in nodes and ref_clean != node_id:
                        # Check if edge doesn't already exist
                        edge_exists = any(
                            e["source"] == node_id and e["target"] == ref_clean 
                            for e in edges
                        )
                        if not edge_exists:
                            edges.append({
                                "source": node_id,
                                "target": ref_clean,
                                "type": "cites"
                            })
    
    # Filter edges to only include valid nodes
    valid_node_ids = set(nodes.keys())
    edges = [e for e in edges if e["source"] in valid_node_ids and e["target"] in valid_node_ids]
    
    # Remove duplicate edges
    seen_edges = set()
    unique_edges = []
    for edge in edges:
        edge_key = (edge["source"], edge["target"])
        if edge_key not in seen_edges:
            seen_edges.add(edge_key)
            unique_edges.append(edge)
    
    nodes_list = list(nodes.values())
    
    logging.info(f"Comprehensive citation network built: {len(nodes_list)} nodes, {len(unique_edges)} edges")
    
    return {
        "nodes": nodes_list,
        "edges": unique_edges,
        "stats": {
            "totalNodes": len(nodes_list),
            "totalEdges": len(unique_edges),
            "rootNodes": sum(1 for n in nodes_list if n.get("isRoot", False)),
            "citationNodes": sum(1 for n in nodes_list if not n.get("isRoot", False))
        }
    }
