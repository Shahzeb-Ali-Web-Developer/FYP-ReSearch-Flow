import re
import pandas as pd
import logging
import uuid
from serpapi.google_search import GoogleSearch
from .pdf_extractor import extract_pdf_text_retry
from ..core.config import settings

def fetch_google_papers_serpapi(topic, limit=20, extract_content=False):
    """
    Fetch papers from Google Scholar via SerpAPI.
    Set extract_content=True to download PDFs (slow!)
    """
    api_key = settings.SERPAPI_KEY
    if not api_key:
        logging.error("SerpAPI key missing")
        return pd.DataFrame()

    params = {
        "engine": "google_scholar",
        "q": topic,  # Remove filetype:pdf to get more results
        "api_key": api_key,
        "num": min(limit * 2, 20)  # SerpAPI has limits
    }

    logging.info(f"Fetching Google Scholar papers for: {topic}")

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        organic = results.get("organic_results", [])
        
        if not organic:
            logging.warning(f"No results from Google Scholar for: {topic}")
            return pd.DataFrame()

        papers = []
        for r in organic:
            pub = r.get("publication_info", {})
            authors = [a.get('name', 'N/A') for a in pub.get('authors', [])] if pub.get('authors') else []
            
            summary = pub.get('summary', '')
            year_match = re.search(r'\b(19|20)\d{2}\b', summary)
            year = int(year_match.group(0)) if year_match else None
            
            url = r.get('link', '')
            
            # Only extract PDF content if requested AND it's a PDF link
            content = ''
            if extract_content and url and url.lower().endswith('.pdf'):
                logging.info(f"Extracting PDF for: {r.get('title', 'Unknown')}")
                content = extract_pdf_text_retry(url)

            paper = {
                'paperId': 'str(uuid.uuid4())',
                'title': r.get('title', 'N/A'),
                'abstract': r.get('snippet', 'N/A'),
                'authors': authors,
                'url': url,
                'year': year,
                'venue': summary.split(' - ')[1] if ' - ' in summary else 'N/A',
                'publicationTypes': [],
                'citationCount': r.get('inline_links', {}).get('cited_by', {}).get('total', 0),
                'referenceCount': 0,
                'isOpenAccess': url.lower().endswith('.pdf') if url else False,
                'openAccessPdf': url if (url and url.lower().endswith('.pdf')) else '',
                'externalIds': {},
                'fieldsOfStudy': [],
                'source': 'Google Scholar (SerpAPI)',
                'topic': topic,
                'content': content
            }
            papers.append(paper)
            
            if len(papers) >= limit:
                break

        df = pd.DataFrame(papers)
        logging.info(f"Fetched {len(df)} papers from Google Scholar")
        return df
        
    except Exception as e:
        logging.error(f"Google Scholar error: {str(e)}")
        return pd.DataFrame()