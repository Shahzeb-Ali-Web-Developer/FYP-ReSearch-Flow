"""
arXiv API Service
Handles queries to the arXiv API and parses ATOM XML responses.
"""
import logging
import re
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime

ARXIV_API_BASE = "http://export.arxiv.org/api/query"

# Namespace for ATOM XML
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def _build_arxiv_search_query(query: str) -> str:
    """
    Build a proper arXiv API search query from a user's natural language query.
    
    The arXiv API treats spaces as OR by default, so "deep learning osteoarthritis"
    becomes "all:deep OR all:learning OR all:osteoarthritis" — returning hundreds of
    thousands of irrelevant results.
    
    This function intelligently groups terms and uses AND + quoted phrases to produce
    highly relevant results, matching how the arXiv website handles searches.
    
    Strategy:
      1. Detect quoted phrases the user explicitly provided (e.g., "deep learning")
      2. Try to detect well-known multi-word concepts (e.g., "deep learning",
         "machine learning", "neural network")
      3. Remaining single words become individual terms
      4. Each term/phrase is searched in BOTH title (ti:) and abstract (abs:)
      5. All term groups are combined with AND
    
    Example:
      Input:  "deep learning osteoarthritis"
      Output: (ti:"deep learning" OR abs:"deep learning") AND (ti:"osteoarthritis" OR abs:"osteoarthritis")
    """
    query = query.strip()
    if not query:
        return "all:*"
    
    # Step 1: Extract explicitly quoted phrases
    explicit_phrases = re.findall(r'"([^"]+)"', query)
    # Remove quoted phrases from the remaining query
    remaining = re.sub(r'"[^"]+"', ' ', query).strip()
    
    # Step 2: Known multi-word academic concepts to detect and group
    known_phrases = [
        "deep learning", "machine learning", "transfer learning",
        "reinforcement learning", "federated learning", "contrastive learning",
        "self supervised learning", "semi supervised learning", "unsupervised learning",
        "supervised learning", "active learning", "meta learning", "curriculum learning",
        "neural network", "neural networks", "convolutional neural network",
        "recurrent neural network", "graph neural network", "generative adversarial network",
        "natural language processing", "computer vision", "object detection",
        "image segmentation", "image classification", "semantic segmentation",
        "instance segmentation", "anomaly detection", "change detection",
        "feature extraction", "data augmentation", "knowledge distillation",
        "attention mechanism", "transformer model",
        "knee osteoarthritis", "hip osteoarthritis",
        "rheumatoid arthritis", "medical imaging", "clinical trial",
        "electronic health records", "health records",
        "large language model", "large language models",
        "language model", "language models",
        "artificial intelligence", "support vector machine",
    ]
    
    detected_phrases = []
    remaining_lower = remaining.lower()
    
    # Sort by length descending so longer phrases match first
    for phrase in sorted(known_phrases, key=len, reverse=True):
        if phrase in remaining_lower:
            detected_phrases.append(phrase)
            # Remove the matched phrase from remaining (case-insensitive)
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            remaining = pattern.sub(' ', remaining, count=1).strip()
            remaining_lower = remaining.lower()
    
    # Step 3: Remaining individual words (filter out very short/common words)
    stop_words = {"a", "an", "the", "in", "on", "of", "for", "and", "or", "with", "to", "from", "by", "is", "are", "was", "were", "be", "been", "being", "using", "based"}
    single_words = [w for w in remaining.split() if len(w) > 1 and w.lower() not in stop_words]
    
    # Step 4: Combine all terms
    all_terms = list(explicit_phrases) + list(detected_phrases) + single_words
    
    if not all_terms:
        return f"all:{query}"
    
    # Step 5: Build the query — each term searches title OR abstract, joined by AND
    parts = []
    for term in all_terms:
        # Quote multi-word terms
        if ' ' in term:
            parts.append(f'(ti:"{term}" OR abs:"{term}")')
        else:
            parts.append(f'(ti:{term} OR abs:{term})')
    
    search_query = " AND ".join(parts)
    logging.info(f"Built arXiv search query: {search_query}")
    return search_query


def fetch_arxiv_papers(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Fetch papers from arXiv API and parse ATOM XML response.
    
    Args:
        query: Search query/topic
        limit: Maximum number of results to return (max 2000 for arXiv)
    
    Returns:
        List of paper dictionaries with arXiv-specific fields
    """
    logging.info(f"Fetching arXiv papers for query: {query}, limit: {limit}")
    
    try:
        # Build arXiv API query with proper AND/phrase handling
        search_query = _build_arxiv_search_query(query)
        
        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": min(limit, 2000),  # arXiv API limit
            "sortBy": "relevance",
            "sortOrder": "descending"
        }
        
        response = requests.get(ARXIV_API_BASE, params=params, timeout=30)
        response.raise_for_status()
        
        # Parse XML response
        root = ET.fromstring(response.content)
        
        papers = []
        entries = root.findall("atom:entry", ATOM_NS)
        
        for entry in entries:
            paper = _parse_arxiv_entry(entry)
            if paper:
                papers.append(paper)
        
        logging.info(f"Successfully fetched {len(papers)} papers from arXiv")
        return papers
        
    except requests.exceptions.RequestException as e:
        logging.error(f"arXiv API error: {str(e)}")
        return []
    except ET.ParseError as e:
        logging.error(f"Failed to parse arXiv XML response: {str(e)}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error in fetch_arxiv_papers: {str(e)}")
        return []


def _parse_arxiv_entry(entry: ET.Element) -> Optional[Dict[str, Any]]:
    """
    Parse a single arXiv entry from ATOM XML.
    
    Args:
        entry: XML element representing one arXiv paper
    
    Returns:
        Dictionary with paper data or None if parsing fails
    """
    try:
        # Extract arXiv ID (from id element, format: http://arxiv.org/abs/1234.5678v1)
        arxiv_id_elem = entry.find("atom:id", ATOM_NS)
        if arxiv_id_elem is None or arxiv_id_elem.text is None:
            return None
        
        arxiv_url = arxiv_id_elem.text.strip()
        # Extract ID: e.g., "1234.5678v1" from "http://arxiv.org/abs/1234.5678v1"
        arxiv_id = arxiv_url.split("/")[-1] if "/" in arxiv_url else arxiv_url
        
        # Title
        title_elem = entry.find("atom:title", ATOM_NS)
        title = title_elem.text.strip().replace("\n", " ") if title_elem is not None and title_elem.text else "Untitled"
        
        # Authors
        authors = []
        for author in entry.findall("atom:author", ATOM_NS):
            name_elem = author.find("atom:name", ATOM_NS)
            if name_elem is not None and name_elem.text:
                authors.append(name_elem.text.strip())
        
        # Published date
        published_elem = entry.find("atom:published", ATOM_NS)
        published_date = None
        if published_elem is not None and published_elem.text:
            try:
                # Parse ISO 8601 format: 2024-01-15T10:30:00Z
                published_date = datetime.fromisoformat(
                    published_elem.text.replace("Z", "+00:00")
                ).isoformat()
            except (ValueError, AttributeError):
                published_date = published_elem.text.strip()
        
        # Updated date (often more reliable)
        updated_elem = entry.find("atom:updated", ATOM_NS)
        updated_date = None
        if updated_elem is not None and updated_elem.text:
            try:
                updated_date = datetime.fromisoformat(
                    updated_elem.text.replace("Z", "+00:00")
                ).isoformat()
            except (ValueError, AttributeError):
                updated_date = updated_elem.text.strip()
        
        # Use updated_date if published_date is not available
        date = published_date or updated_date
        
        # Abstract
        summary_elem = entry.find("atom:summary", ATOM_NS)
        abstract = summary_elem.text.strip().replace("\n", " ") if summary_elem is not None and summary_elem.text else ""
        
        # PDF link (construct from arXiv ID)
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        
        # Abstract page link
        abstract_url = f"https://arxiv.org/abs/{arxiv_id}"
        
        # Categories (subject classification)
        categories = []
        for category in entry.findall("atom:category", ATOM_NS):
            term = category.get("term")
            if term:
                categories.append(term)
        
        paper = {
            "arxiv_id": arxiv_id,
            "title": title,
            "authors": authors,
            "published_date": date,
            "abstract": abstract,
            "pdf_url": pdf_url,
            "abstract_url": abstract_url,
            "categories": categories,
            "source": "arXiv"
        }
        
        return paper
        
    except Exception as e:
        logging.warning(f"Error parsing arXiv entry: {str(e)}")
        return None


