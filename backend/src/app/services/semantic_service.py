import requests
import pandas as pd
import logging
from ..core.config import settings
from .pdf_extractor import extract_pdf_text_retry

def fetch_semantic_papers(topic, limit=20, extract_content=False):
    """
    Fetch papers from Semantic Scholar.
    Set extract_content=True to download PDFs (slow!)
    """
    api_key = settings.SEMANTIC_KEY
    if not api_key:
        logging.error("No Semantic Scholar API key provided.")
        return pd.DataFrame()

    url = 'https://api.semanticscholar.org/graph/v1/paper/search'
    headers = {'x-api-key': api_key}
    params = {
        'query': topic,
        'limit': limit,
        'fields': 'paperId,title,abstract,authors,url,year,venue,publicationTypes,citationCount,referenceCount,isOpenAccess,openAccessPdf,externalIds,fieldsOfStudy'
    }

    logging.info(f"Fetching Semantic Scholar papers for: {topic}")
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json().get('data', [])
        
        if not data:
            logging.warning(f"No results from Semantic Scholar for: {topic}")
            return pd.DataFrame()

        papers = []
        for p in data:
            paper = {
                'paperId': p.get('paperId', ''),
                'title': p.get('title', 'N/A'),
                'abstract': p.get('abstract', 'N/A'),
                'authors': [a['name'] for a in p.get('authors', [])] if p.get('authors') else [],
                'url': p.get('url', ''),
                'year': p.get('year'),
                'venue': p.get('venue', ''),
                'publicationTypes': p.get('publicationTypes', []),
                'citationCount': p.get('citationCount', 0),
                'referenceCount': p.get('referenceCount', 0),
                'isOpenAccess': p.get('isOpenAccess', False),
                'openAccessPdf': p.get('openAccessPdf', {}).get('url', '') if p.get('openAccessPdf') else '',
                'externalIds': p.get('externalIds', {}),
                'fieldsOfStudy': p.get('fieldsOfStudy', []),
                'source': 'Semantic Scholar',
                'topic': topic,
                'content': ''
            }

            # Only extract PDF if explicitly requested
            if extract_content and paper['isOpenAccess'] and paper['openAccessPdf']:
                logging.info(f"Extracting PDF for: {paper['title']}")
                paper['content'] = extract_pdf_text_retry(paper['openAccessPdf'])

            papers.append(paper)

        df = pd.DataFrame(papers)
        logging.info(f"Fetched {len(df)} papers from Semantic Scholar")
        return df

    except requests.exceptions.RequestException as e:
        logging.error(f"Semantic Scholar API error: {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        logging.error(f"Unexpected error in fetch_semantic_papers: {str(e)}")
        return pd.DataFrame()