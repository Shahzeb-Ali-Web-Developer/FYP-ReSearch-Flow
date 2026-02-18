from ..db.client_supabase import supabase
from datetime import datetime
import pandas as pd
import json
import logging
import time

def store_to_supabase(df, topic):
    """Store papers to Supabase in batches with retry logic"""
    if df.empty:
        print("No papers to store.")
        logging.warning("Attempted to store empty DataFrame")
        return 0
    
    # Check if Supabase is configured
    if supabase is None:
        logging.warning("Supabase not configured. Skipping database storage.")
        print("[WARN] Supabase not configured. Papers will not be saved to database.")
        return 0
    
    # Ensure lowercase column names
    df.columns = df.columns.str.lower()
    
    # Prepare all records first
    records = []
    
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
            
            # Handle institutions (list)
            institutions = row.get("institutions", [])
            if isinstance(institutions, str):
                try:
                    institutions = json.loads(institutions)
                except:
                    institutions = [institutions] if institutions else []
            elif not isinstance(institutions, list):
                institutions = [] if pd.isna(institutions) else []
            
            # Handle referencedWorks (list of OpenAlex IDs)
            referencedworks = row.get("referencedworks", [])
            if isinstance(referencedworks, str):
                try:
                    referencedworks = json.loads(referencedworks)
                except:
                    referencedworks = [referencedworks] if referencedworks else []
            elif not isinstance(referencedworks, list):
                referencedworks = []
            
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
                "referencedworks": referencedworks,  # JSON array of OpenAlex IDs
                "isopenaccess": bool(row.get("isopenaccess", False)),
                "openaccesspdf": row.get("openaccesspdf"),
                "externalids": externalids,
                "fieldsofstudy": fieldsofstudy,
                "institutions": institutions,  # JSON array of institution names
                "source": row.get("source", "Unknown"),
                "topic": topic,
                "content": str(row.get("content", ""))[:1000000],  # Limit to 1MB
                "inserted_at": datetime.now().isoformat()
            }
            
            records.append(record)
            
        except Exception as e:
            logging.error(f"Error preparing record {row.get('title', 'Unknown')}: {str(e)}")
    
    # Check if we have records to insert
    if not records:
        logging.warning("No valid records to insert")
        return 0
    
    # Batch insert with retry logic
    inserted_count = 0
    errors = 0
    batch_size = 50  # Smaller batches for better reliability
    
    print(f"Preparing to insert {len(records)} papers in batches of {batch_size}...")
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(records) + batch_size - 1) // batch_size
        
        print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} papers)...")
        
        # Try batch insert with retries
        success = False
        for attempt in range(3):
            try:
                response = supabase.table("research_papers").upsert(
                    batch,
                    returning="minimal",  # Don't return data for speed
                    count="exact"  # Get count of inserted records
                ).execute()
                
                inserted_count += len(batch)
                logging.info(f"[OK] Batch {batch_num} inserted successfully: {len(batch)} papers")
                print(f"[OK] Batch {batch_num} inserted successfully")
                success = True
                break
                
            except Exception as e:
                if attempt < 2:  # Will retry
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s
                    logging.warning(f"Batch {batch_num} attempt {attempt + 1} failed, retrying in {wait_time}s: {str(e)}")
                    print(f"[WARN] Batch {batch_num} attempt {attempt + 1} failed, retrying...")
                    time.sleep(wait_time)
                else:  # Last attempt failed
                    logging.error(f"[ERROR] Batch {batch_num} failed after 3 attempts: {str(e)}")
                    print(f"[ERROR] Batch {batch_num} failed after 3 attempts")
        
        # If batch insert failed, try individual inserts
        if not success:
            print(f"Trying individual inserts for batch {batch_num}...")
            for record in batch:
                try:
                    supabase.table("research_papers").upsert(record).execute()
                    inserted_count += 1
                    logging.info(f"[OK] Individual insert: {record.get('title')}")
                except Exception as e:
                    errors += 1
                    logging.error(f"[ERROR] Failed to insert {record.get('title')}: {str(e)}")
                    print(f"[ERROR] Failed: {record.get('title')[:50]}...")
        
        # Small delay between batches to avoid rate limits
        if i + batch_size < len(records):
            time.sleep(0.5)
    
    print(f"\n{'='*60}")
    print(f"Storage complete: {inserted_count} inserted, {errors} failed")
    print(f"{'='*60}\n")
    
    logging.info(f"Final: {inserted_count} successful, {errors} failed out of {len(records)} total")
    return inserted_count