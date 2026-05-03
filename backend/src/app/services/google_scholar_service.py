"""
Google Scholar API Service
Handles queries to Google Scholar using SerpAPI.
"""
import logging
import os
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..core.config import settings

# SerpAPI endpoint for Google Scholar
SERPAPI_BASE = "https://serpapi.com/search"


def fetch_google_scholar_papers(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Fetch papers from Google Scholar using SerpAPI.
    
    Args:
        query: Search query/topic
        limit: Maximum number of results to return
    
    Returns:
        List of paper dictionaries with Google Scholar-specific fields
    """
    # Check if SerpAPI key is configured
    serpapi_key = (
        getattr(settings, "SERPAPI_API_KEY", None)
        or os.getenv("SERPAPI_API_KEY")
        or os.getenv("SERPAI_API_KEY")
    )
    if not serpapi_key:
        logging.warning("SERPAPI_API_KEY not configured, Google Scholar search unavailable")
        return []
    
    logging.info(f"Fetching Google Scholar papers for query: {query}, limit: {limit}")
    
    try:
        params = {
            "engine": "google_scholar",
            "q": query,
            "api_key": serpapi_key,
            "num": min(limit, 100)  # SerpAPI limit per page
        }
        
        all_papers = []
        start_page = 0
        
        while len(all_papers) < limit:
            if start_page > 0:
                params["start"] = start_page
            
            response = requests.get(SERPAPI_BASE, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            organic_results = data.get("organic_results", [])
            
            if not organic_results:
                break
            
            for result in organic_results:
                paper = _parse_google_scholar_result(result)
                if paper:
                    all_papers.append(paper)
                    if len(all_papers) >= limit:
                        break
            
            # Check if there are more pages
            if len(organic_results) < params["num"] or len(all_papers) >= limit:
                break
            
            start_page += len(organic_results)
        
        logging.info(f"Successfully fetched {len(all_papers)} papers from Google Scholar")
        return all_papers
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            logging.error("SerpAPI authentication failed. Check API key.")
        elif e.response.status_code == 429:
            logging.error("SerpAPI rate limit exceeded.")
        else:
            logging.error(f"SerpAPI HTTP error: {str(e)}")
        return []
    except requests.exceptions.RequestException as e:
        logging.error(f"SerpAPI error: {str(e)}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error in fetch_google_scholar_papers: {str(e)}")
        return []


def _parse_google_scholar_result(result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse a Google Scholar result into our paper format.
    
    Args:
        result: Single result from SerpAPI Google Scholar
    
    Returns:
        Parsed paper dictionary or None if parsing fails
    """
    try:
        # Title
        title = result.get("title", "")
        if not title:
            return None
        
        # Authors
        authors = []
        authors_list = result.get("publication_info", {}).get("authors", [])
        if authors_list:
            for author in authors_list:
                if isinstance(author, dict):
                    author_name = author.get("name", "")
                    if author_name:
                        authors.append(author_name)
                elif isinstance(author, str):
                    authors.append(author)
        
        # If no authors from publication_info, try result.authors
        if not authors:
            authors_data = result.get("authors", [])
            for author in authors_data:
                if isinstance(author, dict):
                    authors.append(author.get("name", ""))
                elif isinstance(author, str):
                    authors.append(author)
        
        # Year
        year = None
        publication_info = result.get("publication_info", {})
        if publication_info:
            summary = publication_info.get("summary", "")
            # Try to extract year from summary (e.g., "2023")
            import re
            year_match = re.search(r'\b(19|20)\d{2}\b', summary)
            if year_match:
                try:
                    year = int(year_match.group())
                except:
                    pass
        
        # Abstract/snippet
        abstract = result.get("snippet", "") or ""
        
        # PDF URL - Google Scholar often has PDF links
        pdf_url = None
        pdf_link = result.get("resources", [])
        if pdf_link:
            for resource in pdf_link:
                if isinstance(resource, dict) and resource.get("file_format") == "PDF":
                    pdf_url = resource.get("link")
                    break
        
        # If no PDF in resources, check link
        if not pdf_url:
            link = result.get("link", "")
            if link and link.endswith('.pdf'):
                pdf_url = link
        
        # Paper URL
        url = result.get("link") or result.get("result_id", "")
        if url and not url.startswith("http"):
            url = f"https://scholar.google.com{url}" if url.startswith("/") else f"https://scholar.google.com/{url}"
        
        # Citation count
        citation_count = 0
        cited_by = result.get("inline_links", {}).get("cited_by", {})
        if cited_by:
            citation_count = cited_by.get("total", 0) or 0
        
        # Venue/Publication
        venue = ""
        publication_info = result.get("publication_info", {})
        if publication_info:
            summary = publication_info.get("summary", "")
            if summary:
                venue = summary
        
        # Result ID (Google Scholar ID)
        result_id = result.get("result_id", "")
        
        paper = {
            "google_scholar_id": result_id,
            "title": title,
            "authors": authors,
            "published_date": f"{year}-01-01" if year else None,
            "year": year,
            "abstract": abstract,
            "pdf_url": pdf_url,
            "url": url,
            "venue": venue,
            "citationCount": citation_count,
            "source": "Google Scholar",
            "isOpenAccess": bool(pdf_url)
        }
        
        return paper
        
    except Exception as e:
        logging.warning(f"Error parsing Google Scholar result: {str(e)}")
        return None


