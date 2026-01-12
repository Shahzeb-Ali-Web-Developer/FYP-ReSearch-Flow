"""
arXiv API Service
Handles queries to the arXiv API and parses ATOM XML responses.
"""
import logging
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime

ARXIV_API_BASE = "http://export.arxiv.org/api/query"

# Namespace for ATOM XML
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


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
        # Build arXiv API query
        params = {
            "search_query": f"all:{query}",
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


