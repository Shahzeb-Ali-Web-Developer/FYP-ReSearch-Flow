"""
PubMed Central (PMC) API Service
Handles queries to the NCBI E-utilities API for PMC articles.
"""
import logging
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime

PMC_EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PMC_BASE_URL = "https://www.ncbi.nlm.nih.gov/pmc/articles/"


def fetch_pmc_papers(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Fetch papers from PubMed Central using E-utilities API.
    
    Args:
        query: Search query/topic
        limit: Maximum number of results to return (max: 10000)
    
    Returns:
        List of paper dictionaries with PMC-specific fields
    """
    logging.info(f"Fetching PMC papers for query: {query}, limit: {limit}")
    
    try:
        # Step 1: Search for PMC IDs
        search_params = {
            "db": "pmc",
            "term": query,
            "retmax": min(limit, 10000),  # E-utilities max
            "retmode": "xml",
            "usehistory": "y"
        }
        
        search_url = f"{PMC_EUTILS_BASE}/esearch.fcgi"
        search_response = requests.get(search_url, params=search_params, timeout=30)
        search_response.raise_for_status()
        
        # Parse search results to get PMC IDs
        search_root = ET.fromstring(search_response.content)
        pmc_ids = [id_elem.text for id_elem in search_root.findall(".//Id")]
        
        if not pmc_ids:
            logging.info("No PMC IDs found for query")
            return []
        
        # Limit to requested number
        pmc_ids = pmc_ids[:limit]
        
        # Step 2: Fetch full records for each PMC ID
        papers = []
        batch_size = 100  # EFetch can handle up to 100 IDs at a time
        
        for i in range(0, len(pmc_ids), batch_size):
            batch_ids = pmc_ids[i:i + batch_size]
            id_string = ",".join(batch_ids)
            
            fetch_params = {
                "db": "pmc",
                "id": id_string,
                "retmode": "xml",
                "rettype": "abstract"  # Can also use 'full' for full text
            }
            
            fetch_url = f"{PMC_EUTILS_BASE}/efetch.fcgi"
            fetch_response = requests.get(fetch_url, params=fetch_params, timeout=60)
            fetch_response.raise_for_status()
            
            # Parse XML response
            fetch_root = ET.fromstring(fetch_response.content)
            
            # Handle multiple articles (articles are wrapped in <pmc-articleset>)
            for article in fetch_root.findall(".//article"):
                paper = _parse_pmc_article(article, batch_ids[len(papers) - i] if len(papers) - i < len(batch_ids) else None)
                if paper:
                    papers.append(paper)
                    if len(papers) >= limit:
                        break
            
            if len(papers) >= limit:
                break
        
        logging.info(f"Successfully fetched {len(papers)} papers from PMC")
        return papers
        
    except requests.exceptions.HTTPError as e:
        logging.error(f"PMC API HTTP error: {str(e)}")
        return []
    except requests.exceptions.RequestException as e:
        logging.error(f"PMC API error: {str(e)}")
        return []
    except ET.ParseError as e:
        logging.error(f"Failed to parse PMC XML response: {str(e)}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error in fetch_pmc_papers: {str(e)}")
        return []


def _parse_pmc_article(article: ET.Element, pmc_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Parse a PMC article XML element into our paper format.
    
    Args:
        article: XML element representing a PMC article
        pmc_id: Optional PMC ID (if not found in XML)
    
    Returns:
        Parsed paper dictionary or None if parsing fails
    """
    try:
        # Namespace handling for PMC XML
        ns = {
            'x': 'http://www.ncbi.nlm.nih.gov',
            'm': 'http://www.w3.org/1998/Math/MathML'
        }
        
        # Extract PMC ID
        if not pmc_id:
            pmc_id_elem = article.find(".//article-id[@pub-id-type='pmc']")
            if pmc_id_elem is not None and pmc_id_elem.text:
                pmc_id = pmc_id_elem.text
        
        if not pmc_id:
            # Try alternative method
            pmc_id_elem = article.find(".//article-id")
            if pmc_id_elem is not None and pmc_id_elem.text:
                pmc_id = pmc_id_elem.text
        
        if not pmc_id:
            return None  # Skip articles without PMC ID
        
        # Title
        title_elem = article.find(".//article-title")
        title = ""
        if title_elem is not None:
            # Handle title with sub-elements
            if title_elem.text:
                title = title_elem.text.strip()
            else:
                # Extract all text content
                title = "".join(title_elem.itertext()).strip()
        
        if not title or title == "":
            return None  # Skip articles without titles
        
        # Authors
        authors = []
        for contrib in article.findall(".//contrib[@contrib-type='author']"):
            given_name = contrib.findtext(".//given-names", default="")
            surname = contrib.findtext(".//surname", default="")
            if given_name or surname:
                author_name = f"{given_name} {surname}".strip()
                if author_name:
                    authors.append(author_name)
        
        # Published date
        pub_date = None
        year = None
        pub_date_elem = article.find(".//pub-date[@pub-type='ppub']") or article.find(".//pub-date[@pub-type='epub']") or article.find(".//pub-date")
        if pub_date_elem is not None:
            year_elem = pub_date_elem.find("year")
            month_elem = pub_date_elem.find("month")
            day_elem = pub_date_elem.find("day")
            
            if year_elem is not None and year_elem.text:
                year = int(year_elem.text)
                date_parts = [year_elem.text]
                
                if month_elem is not None and month_elem.text:
                    date_parts.append(month_elem.text.zfill(2))
                    if day_elem is not None and day_elem.text:
                        date_parts.append(day_elem.text.zfill(2))
                    else:
                        date_parts.append("01")
                else:
                    date_parts.extend(["01", "01"])
                
                pub_date = "-".join(date_parts)
        
        # Abstract
        abstract = ""
        abstract_elem = article.find(".//abstract")
        if abstract_elem is not None:
            # Extract all text from abstract
            abstract_parts = []
            for para in abstract_elem.findall(".//p"):
                para_text = "".join(para.itertext()).strip()
                if para_text:
                    abstract_parts.append(para_text)
            
            abstract = " ".join(abstract_parts) if abstract_parts else "".join(abstract_elem.itertext()).strip()
        
        # DOI
        doi = None
        doi_elem = article.find(".//article-id[@pub-id-type='doi']")
        if doi_elem is not None and doi_elem.text:
            doi = doi_elem.text
            if not doi.startswith("http"):
                doi = f"https://doi.org/{doi}"
        
        # PDF URL - PMC provides PDFs for open access articles
        pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf/"
        
        # Article URL
        article_url = f"{PMC_BASE_URL}PMC{pmc_id}/"
        
        # Journal
        journal = ""
        journal_elem = article.find(".//journal-title")
        if journal_elem is not None and journal_elem.text:
            journal = journal_elem.text.strip()
        
        # Volume and Issue
        volume = article.findtext(".//volume", default="")
        issue = article.findtext(".//issue", default="")
        
        paper = {
            "pmc_id": pmc_id,
            "title": title,
            "authors": authors,
            "published_date": pub_date,
            "year": year,
            "abstract": abstract,
            "pdf_url": pdf_url,
            "url": article_url,
            "doi": doi,
            "journal": journal,
            "volume": volume,
            "issue": issue,
            "source": "PMC"
        }
        
        return paper
        
    except Exception as e:
        logging.warning(f"Error parsing PMC article: {str(e)}")
        return None

<<<<<<< HEAD

=======
>>>>>>> 19c62c6432f4465bd0724c79e5a8f133d21dc582
