"""
CORE API Service
Handles queries to the CORE API for academic papers.
"""
import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..core.config import settings

CORE_API_BASE = "https://api.core.ac.uk/v3/search/works"


def fetch_core_papers(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Fetch papers from CORE API.
    
    Args:
        query: Search query/topic
        limit: Maximum number of results to return
    
    Returns:
        List of paper dictionaries with CORE-specific fields
    """
    if not settings.CORE_API_KEY:
        logging.error("CORE_API_KEY not configured")
        return []
    
    logging.info(f"Fetching CORE papers for query: {query}, limit: {limit}")
    
    try:
        headers = {
            "Authorization": f"Bearer {settings.CORE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        params = {
            "q": query,
            "limit": min(limit, 100),  # CORE API limit per page
            "offset": 0
        }
        
        all_papers = []
        offset = 0
        
        while len(all_papers) < limit:
            params["offset"] = offset
            params["limit"] = min(limit - len(all_papers), 100)
            
            response = requests.get(CORE_API_BASE, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                break
            
            for result in results:
                paper = _parse_core_result(result)
                if paper:
                    all_papers.append(paper)
                    if len(all_papers) >= limit:
                        break
            
            # Check if there are more results
            if len(results) < params["limit"]:
                break
            
            offset += len(results)
        
        logging.info(f"Successfully fetched {len(all_papers)} papers from CORE")
        return all_papers
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            logging.error("CORE API authentication failed. Check API key.")
        elif e.response.status_code == 429:
            logging.error("CORE API rate limit exceeded.")
        else:
            logging.error(f"CORE API HTTP error: {str(e)}")
        return []
    except requests.exceptions.RequestException as e:
        logging.error(f"CORE API error: {str(e)}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error in fetch_core_papers: {str(e)}")
        return []


def _parse_core_result(result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse a CORE API result into our paper format.
    
    Args:
        result: Single result from CORE API
    
    Returns:
        Parsed paper dictionary or None if parsing fails
    """
    try:
        # Title
        title = result.get("title", "Untitled")
        if not title or title == "Untitled":
            return None  # Skip papers without titles
        
        # Authors
        authors = []
        for author in result.get("authors", []):
            if isinstance(author, dict):
                author_name = author.get("name", "")
                if author_name:
                    authors.append(author_name)
            elif isinstance(author, str):
                authors.append(author)
        
        # Published date
        published_date = None
        if result.get("year"):
            try:
                published_date = f"{result['year']}-01-01"
            except:
                pass
        
        # Abstract
        abstract = result.get("abstract", "") or ""
        
        # PDF URL - CORE provides downloadUrl for PDFs
        pdf_url = None
        download_url = result.get("downloadUrl")
        if download_url:
            pdf_url = download_url
        else:
            # Try to get from fullTextIdentifier
            full_text = result.get("fullTextIdentifier")
            if full_text and full_text.endswith('.pdf'):
                pdf_url = full_text
        
        # Main URL
        url = result.get("url") or result.get("doi") or pdf_url
        
        # DOI
        doi = result.get("doi")
        if doi and not doi.startswith("http"):
            doi = f"https://doi.org/{doi}"
        
        # CORE ID
        core_id = result.get("id")
        
        # Publisher
        publisher = result.get("publisher", "")
        
        # Repository
        repositories = result.get("repositories", [])
        repository = ""
        if repositories and len(repositories) > 0:
            repo = repositories[0]
            if isinstance(repo, dict):
                repository = repo.get("name", "")
            elif isinstance(repo, str):
                repository = repo
        
        # Language
        language = result.get("language", {}).get("name", "") if isinstance(result.get("language"), dict) else ""
        
        paper = {
            "core_id": core_id,
            "title": title,
            "authors": authors,
            "published_date": published_date,
            "year": result.get("year"),
            "abstract": abstract,
            "pdf_url": pdf_url,
            "url": url,
            "doi": doi,
            "publisher": publisher,
            "repository": repository,
            "language": language,
            "source": "CORE"
        }
        
        return paper
        
    except Exception as e:
        logging.warning(f"Error parsing CORE result: {str(e)}")
        return None

