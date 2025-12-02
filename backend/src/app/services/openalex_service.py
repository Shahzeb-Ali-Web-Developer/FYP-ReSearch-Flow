import logging
from typing import List, Dict, Any

import requests
import pandas as pd


OPENALEX_BASE_URL = "https://api.openalex.org"


def _flatten_abstract(abstract_inverted_index: Dict[str, List[int]] | None) -> str:
    """
    OpenAlex stores abstracts as an inverted index: {word: [positions...]}.
    Reconstruct a simple plain-text abstract.
    """
    if not abstract_inverted_index:
        return "N/A"

    # Find maximum position to size the list
    max_pos = max(pos for positions in abstract_inverted_index.values() for pos in positions)
    tokens: List[str] = [""] * (max_pos + 1)

    for word, positions in abstract_inverted_index.items():
        for pos in positions:
            if 0 <= pos < len(tokens):
                tokens[pos] = word

    abstract = " ".join(t for t in tokens if t)
    return abstract.strip() or "N/A"


def fetch_openalex_papers(topic: str, limit: int = 20) -> pd.DataFrame:
    """
    Fetch papers (works) from the OpenAlex API and normalize into a DataFrame
    compatible with the existing clean_and_deduplicate + Paper schema.
    """
    logging.info(f"Fetching OpenAlex works for topic: {topic}, limit: {limit}")

    per_page = min(limit, 50)
    url = f"{OPENALEX_BASE_URL}/works"
    params = {
        "search": topic,
        "per-page": per_page,
        # Sort by relevance then citations to get useful results
        "sort": "relevance_score:desc,cited_by_count:desc",
    }

    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        results: List[Dict[str, Any]] = data.get("results", [])

        if not results:
            logging.warning(f"No results from OpenAlex for topic: {topic}")
            return pd.DataFrame()

        papers: List[Dict[str, Any]] = []
        for w in results[:limit]:
            abstract = _flatten_abstract(w.get("abstract_inverted_index"))

            # Authors
            authorships = w.get("authorships", []) or []
            authors = [
                (a.get("author") or {}).get("display_name", "Unknown Author")
                for a in authorships
            ]

            # Primary location / venue
            primary_location = w.get("primary_location") or {}
            source = primary_location.get("source") or {}

            venue_name = source.get("display_name") or "N/A"

            # Prefer landing_page_url, fallback to OA URL or OpenAlex URL
            landing_page = primary_location.get("landing_page_url") or ""
            oa_info = w.get("open_access") or {}
            oa_url = oa_info.get("oa_url") or ""
            openalex_id = w.get("id") or ""

            url_final = landing_page or oa_url or openalex_id

            # External IDs (DOI, etc.)
            external_ids = w.get("ids") or {}

            # Concepts as fields of study
            concepts = w.get("concepts") or []
            fields_of_study = [c.get("display_name", "") for c in concepts if c.get("display_name")]

            referenced_works = w.get("referenced_works") or []

            paper = {
                "paperId": w.get("id"),
                "title": w.get("display_name") or "N/A",
                "abstract": abstract,
                "authors": authors,
                "url": url_final,
                "year": w.get("publication_year"),
                "venue": venue_name,
                "publicationTypes": [],  # OpenAlex doesn't directly expose this like Semantic Scholar
                "citationCount": w.get("cited_by_count", 0),
                "referenceCount": len(referenced_works),
                "isOpenAccess": bool(oa_info.get("is_oa", False)),
                "openAccessPdf": oa_url,
                "externalIds": external_ids,
                "fieldsOfStudy": fields_of_study,
                "source": "OpenAlex",
                "topic": topic,
                "content": "",
            }

            papers.append(paper)

        df = pd.DataFrame(papers)
        logging.info(f"Fetched {len(df)} papers from OpenAlex")
        return df

    except requests.exceptions.RequestException as e:
        logging.error(f"OpenAlex API error: {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        logging.error(f"Unexpected error in fetch_openalex_papers: {str(e)}")
        return pd.DataFrame()


