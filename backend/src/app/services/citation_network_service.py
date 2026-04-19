import logging
import re
from typing import List, Dict, Any, Set, Tuple, Optional
import requests
from collections import defaultdict
from datetime import datetime

OPENALEX_BASE_URL = "https://api.openalex.org"
SEMANTIC_SCHOLAR_BASE = "https://api.semanticscholar.org/graph/v1"


def _is_semantic_scholar_id(paper_id: str) -> bool:
    """Check if a paper ID looks like a Semantic Scholar ID (40-char hex string)."""
    return bool(re.match(r'^[0-9a-f]{40}$', str(paper_id).strip()))


def fetch_semantic_scholar_references(paper_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch paper details and references from Semantic Scholar API.
    Returns paper info with 'references' list of paper IDs.
    """
    try:
        url = f"{SEMANTIC_SCHOLAR_BASE}/paper/{paper_id}"
        params = {
            "fields": "paperId,title,authors,year,citationCount,venue,references.paperId,references.title,references.year,references.citationCount,references.authors,references.venue"
        }
        headers = {"User-Agent": "ReSearch-Flow/1.0"}
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logging.warning(f"Failed to fetch Semantic Scholar paper {paper_id}: {str(e)}")
        return None


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


def _enrich_graph_with_metrics(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> None:
    """Computes Influence Score, PageRank, and Citation Velocity for graph nodes."""
    current_year = datetime.now().year
    
    # 1. Initialize & Citation Velocity
    for node in nodes:
        node["inDegree"] = 0
        node["pageRankScore"] = 1.0 / max(1, len(nodes))  # Initial PR is 1/N
        
        year = node.get("year")
        cites = node.get("citationCount", 0)
        if year and isinstance(year, int) and year <= current_year:
            age = max(1, current_year - year)
            node["citationVelocity"] = round(cites / age, 2)
        else:
            node["citationVelocity"] = 0.0

    # 2. In-Degree & Influence Score
    in_degrees = defaultdict(int)
    out_degrees = defaultdict(int)
    for edge in edges:
        in_degrees[edge["target"]] += 1
        out_degrees[edge["source"]] += 1
        
    max_in_degree = max(in_degrees.values()) if in_degrees else 1
    
    for node in nodes:
        nid = node["id"]
        node["inDegree"] = in_degrees[nid]
        node["influenceScore"] = round(in_degrees[nid] / max_in_degree, 4) if max_in_degree > 0 else 0.0
        
    # 3. PageRank Algorithm
    d = 0.85
    num_iterations = 10
    num_nodes = len(nodes)
    
    if num_nodes == 0:
        return
        
    node_map = {n["id"]: n for n in nodes}
    incoming_edges = defaultdict(list)
    for edge in edges:
        incoming_edges[edge["target"]].append(edge["source"])
        
    for _ in range(num_iterations):
        new_pr = {}
        for node in nodes:
            nid = node["id"]
            pr_sum = 0.0
            for source_id in incoming_edges[nid]:
                if source_id in node_map:
                    source_out = out_degrees[source_id]
                    if source_out > 0:
                        pr_sum += node_map[source_id]["pageRankScore"] / source_out
            
            # Formula: (1-d)/N + d * sum
            new_pr[nid] = ((1.0 - d) / num_nodes) + d * pr_sum
            
        for nid, score in new_pr.items():
            node_map[nid]["pageRankScore"] = score
            
    # Normalize PageRank to 0-1 range for frontend mapping
    pr_scores = [n["pageRankScore"] for n in nodes]
    max_pr = max(pr_scores) if pr_scores else 1.0
    for node in nodes:
        node["pageRankScore"] = round(node["pageRankScore"] / max_pr, 4) if max_pr > 0 else 0.0


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
    
    _enrich_graph_with_metrics(nodes_list, edges)
    
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
    Build an interconnected citation network from search results.
    Auto-detects whether papers are from Semantic Scholar or OpenAlex and uses the correct API.
    """
    logging.info(f"Building citation network from {len(papers)} papers, max_depth={max_depth}, max_nodes={max_nodes}")
    
    # Detect paper source by checking IDs
    sample_ids = [p.get("paperId") or p.get("id", "") for p in papers[:3]]
    use_semantic_scholar = any(_is_semantic_scholar_id(pid) for pid in sample_ids if pid)
    
    if use_semantic_scholar:
        logging.info("Detected Semantic Scholar paper IDs — using Semantic Scholar API for references")
        return _build_network_semantic_scholar(papers, max_depth, max_nodes)
    else:
        logging.info("Using OpenAlex API for references")
        return _build_network_openalex(papers, max_depth, max_nodes)


def _build_network_semantic_scholar(papers: List[Dict[str, Any]], max_depth: int = 1, max_nodes: int = 50) -> Dict[str, Any]:
    """Build citation network using Semantic Scholar API."""
    nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []
    visited: Set[str] = set()
    
    # Step 1: Add root papers
    for paper in papers:
        paper_id = paper.get("paperId") or paper.get("id")
        if not paper_id or paper_id in visited:
            continue
        
        if len(nodes) >= max_nodes:
            break
            
        visited.add(paper_id)
        
        # Extract author names (handle both string list and object list)
        authors = paper.get("authors", [])
        if authors and isinstance(authors[0], dict):
            authors = [a.get("name", "Unknown") for a in authors[:3]]
        else:
            authors = authors[:3]
        
        nodes[paper_id] = {
            "id": paper_id,
            "label": (paper.get("title") or "Unknown Title")[:100],
            "title": paper.get("title", "Unknown Title"),
            "year": paper.get("year"),
            "citationCount": paper.get("citationCount", 0),
            "authors": authors,
            "venue": paper.get("venue", "N/A"),
            "isRoot": True
        }
    
    # Step 2: Fetch references for root papers (1 level deep)
    if max_depth >= 1:
        root_ids = list(nodes.keys())
        for paper_id in root_ids:
            if len(nodes) >= max_nodes:
                break
            
            ref_data = fetch_semantic_scholar_references(paper_id)
            if not ref_data:
                continue
            
            references = ref_data.get("references") or []
            for ref in references[:8]:  # Limit refs per paper for speed
                if len(nodes) >= max_nodes:
                    break
                    
                ref_id = ref.get("paperId")
                if not ref_id:
                    continue
                
                # Add edge
                edges.append({
                    "source": paper_id,
                    "target": ref_id,
                    "type": "cites"
                })
                
                # Add referenced paper as node if not already added
                if ref_id not in visited:
                    visited.add(ref_id)
                    
                    ref_authors = ref.get("authors") or []
                    if ref_authors and isinstance(ref_authors[0], dict):
                        ref_authors = [a.get("name", "Unknown") for a in ref_authors[:3]]
                    else:
                        ref_authors = ref_authors[:3]
                    
                    nodes[ref_id] = {
                        "id": ref_id,
                        "label": (ref.get("title") or "Unknown Title")[:100],
                        "title": ref.get("title", "Unknown Title"),
                        "year": ref.get("year"),
                        "citationCount": ref.get("citationCount", 0),
                        "authors": ref_authors,
                        "venue": ref.get("venue", "N/A"),
                        "isRoot": False
                    }
    
    # Step 3: Find cross-references between existing nodes
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
    
    _enrich_graph_with_metrics(nodes_list, unique_edges)
    
    logging.info(f"Semantic Scholar citation network: {len(nodes_list)} nodes, {len(unique_edges)} edges")
    
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


def _build_network_openalex(papers: List[Dict[str, Any]], max_depth: int = 1, max_nodes: int = 50) -> Dict[str, Any]:
    """Build citation network using OpenAlex API (original logic)."""
    nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []
    visited: Set[str] = set()
    root_ids: Set[str] = set()
    to_process: List[Tuple[str, int, str]] = []

    # Step 1: Add root papers
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
    
    # Step 2: Build network by exploring citations
    while to_process and len(nodes) < max_nodes:
        current_id, depth, relation = to_process.pop(0)
        
        if depth >= max_depth:
            continue
        
        work = fetch_work_details(current_id)
        if not work:
            continue
        
        referenced_works = work.get("referenced_works", [])[:10]
        
        for ref_id in referenced_works:
            if len(nodes) >= max_nodes:
                break
            
            if ref_id.startswith("https://openalex.org/"):
                ref_id = ref_id.replace("https://openalex.org/", "")
            
            if current_id in nodes:
                edges.append({
                    "source": current_id,
                    "target": ref_id,
                    "type": "cites"
                })
            
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
                    if depth < max_depth - 1:
                        to_process.append((ref_id, depth + 1, "reference"))
    
    # Filter and deduplicate edges
    valid_node_ids = set(nodes.keys())
    edges = [e for e in edges if e["source"] in valid_node_ids and e["target"] in valid_node_ids]
    
    seen_edges = set()
    unique_edges = []
    for edge in edges:
        edge_key = (edge["source"], edge["target"])
        if edge_key not in seen_edges:
            seen_edges.add(edge_key)
            unique_edges.append(edge)
    
    nodes_list = list(nodes.values())
    
    _enrich_graph_with_metrics(nodes_list, unique_edges)
    
    logging.info(f"OpenAlex citation network: {len(nodes_list)} nodes, {len(unique_edges)} edges")
    
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

