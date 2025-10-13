import pandas as pd
import logging

def clean_and_deduplicate(df, topic):
    if df.empty:
        logging.warning("Empty DataFrame passed to clean_and_deduplicate")
        return df

    logging.info(f"Cleaning {len(df)} papers for topic: {topic}")

    # Define expected columns
    expected_cols = [
        'paperId', 'title', 'abstract', 'authors', 'url', 'year', 'venue',
        'publicationTypes', 'citationCount', 'referenceCount', 'isOpenAccess',
        'openAccessPdf', 'externalIds', 'fieldsOfStudy', 'source', 'topic', 'content'
    ]
    
    for col in expected_cols:
        if col not in df.columns:
            df[col] = None

    # Clean string fields
    df['title'] = df['title'].fillna('N/A').astype(str).str.strip()
    df['abstract'] = df['abstract'].fillna('N/A').astype(str).str.strip()
    df['content'] = df['content'].fillna('').astype(str).str.strip()
    df['url'] = df['url'].fillna('N/A').astype(str).str.strip()
    df['venue'] = df['venue'].fillna('N/A').astype(str).str.strip()
    df['topic'] = topic

    # Handle list/dict fields
    df['authors'] = df['authors'].apply(lambda x: x if isinstance(x, list) else [])
    df['publicationTypes'] = df['publicationTypes'].apply(lambda x: x if isinstance(x, list) else [])
    df['fieldsOfStudy'] = df['fieldsOfStudy'].apply(lambda x: x if isinstance(x, list) else [])
    df['externalIds'] = df['externalIds'].apply(lambda x: x if isinstance(x, dict) else {})

    # Handle numeric fields
    df['year'] = pd.to_numeric(df['year'], errors='coerce').fillna(0).astype(int)
    df['citationCount'] = pd.to_numeric(df['citationCount'], errors='coerce').fillna(0).astype(int)
    df['referenceCount'] = pd.to_numeric(df['referenceCount'], errors='coerce').fillna(0).astype(int)
    df['isOpenAccess'] = df['isOpenAccess'].fillna(False).astype(bool)
    df['openAccessPdf'] = df['openAccessPdf'].fillna('')

    # Remove duplicates by title
    initial_count = len(df)
    df = df.drop_duplicates(subset=['title'], keep='first')
    removed = initial_count - len(df)
    
    if removed > 0:
        logging.info(f"Removed {removed} duplicate papers")

    logging.info(f"Cleaning complete: {len(df)} papers remaining")
    return df