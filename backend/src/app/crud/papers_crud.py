from ..db.client_supabase import supabase
from datetime import datetime
import pandas as pd
import json
import logging

def store_to_supabase(df, topic):
    if df.empty:
        print("No papers to store.")
        logging.warning("Attempted to store empty DataFrame")
        return 0
    
    inserted_count = 0
    errors = 0
    
    # Ensure lowercase column names
    df.columns = df.columns.str.lower()
    
    for _, row in df.iterrows():
        try:
            # Handle authors (list)
            authors = row.get("authors")
            if isinstance(authors, str):
                try:
                    authors = json.loads(authors)
                except:
                    authors = [authors]
            elif not isinstance(authors, list):
                authors = [] if pd.isna(authors) else [str(authors)]
            
            # Handle externalIds (dict)
            externalids = row.get("externalids", {})
            if isinstance(externalids, str):
                try:
                    externalids = json.loads(externalids)
                except:
                    externalids = {}
            elif not isinstance(externalids, dict):
                externalids = {}
            
            # Handle publicationTypes (list)
            publicationtypes = row.get("publicationtypes", [])
            if isinstance(publicationtypes, str):
                try:
                    publicationtypes = json.loads(publicationtypes)
                except:
                    publicationtypes = [publicationtypes]
            elif not isinstance(publicationtypes, list):
                publicationtypes = []
            
            # Handle fieldsOfStudy (list)
            fieldsofstudy = row.get("fieldsofstudy", [])
            if isinstance(fieldsofstudy, str):
                try:
                    fieldsofstudy = json.loads(fieldsofstudy)
                except:
                    fieldsofstudy = [fieldsofstudy]
            elif not isinstance(fieldsofstudy, list):
                fieldsofstudy = []
            
            record = {
                "paperid": row.get("paperid"),
                "title": row.get("title", "N/A"),
                "abstract": row.get("abstract", "N/A"),
                "authors": authors,
                "url": row.get("url"),
                "year": int(row["year"]) if pd.notna(row.get("year")) else None,
                "venue": row.get("venue"),
                "publicationtypes": publicationtypes,
                "citationcount": int(row.get("citationcount", 0)) if pd.notna(row.get("citationcount")) else 0,
                "referencecount": int(row.get("referencecount", 0)) if pd.notna(row.get("referencecount")) else 0,
                "isopenaccess": bool(row.get("isopenaccess", False)),
                "openaccesspdf": row.get("openaccesspdf"),
                "externalids": externalids,
                "fieldsofstudy": fieldsofstudy,
                "source": row.get("source", "Unknown"),
                "topic": topic,
                "content": str(row.get("content", ""))[:1000000],  # Limit to 1MB
                "inserted_at": datetime.now().isoformat()
            }
            
            response = supabase.table("research_papers").upsert(record).execute()
            
            if response.data:
                inserted_count += 1
                logging.info(f"Inserted: {record['title']}")
            else:
                errors += 1
                logging.error(f"Failed to insert {record['title']}: {response}")
                
        except Exception as e:
            errors += 1
            logging.error(f"Exception inserting {row.get('title', 'Unknown')}: {str(e)}")
            print(f"Error inserting paper: {str(e)}")
    
    print(f"Inserted {inserted_count} papers. Failed: {errors}")
    logging.info(f"Storage complete: {inserted_count} successful, {errors} failed")
    return inserted_count