"""
PDF Service
Handles downloading and text extraction from PDFs using PyMuPDF.
"""
import logging
import requests
import re
from typing import Optional, Tuple
import fitz  # PyMuPDF


def download_pdf(url: str, timeout: int = 30) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Download PDF from URL.
    
    Args:
        url: PDF URL
        timeout: Request timeout in seconds
    
    Returns:
        Tuple of (PDF content as bytes, error_message)
        If successful: (bytes, None)
        If failed: (None, error_message)
    """
    try:
        # EXACT headers from your working snippet
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # arXiv specific: try export.arxiv.org if main domain fails
        if 'arxiv.org' in url and 'export' not in url:
            # We'll try the export domain as it is much more bot-friendly
            url = url.replace('arxiv.org', 'export.arxiv.org')
            logging.info(f"Using arXiv export domain for download: {url}")

        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        response.raise_for_status()
        
        # Check if it's actually a PDF
        content_type = response.headers.get('Content-Type', '').lower()
        if 'pdf' in content_type or response.content[:4] == b'%PDF':
            return (response.content, None)
        else:
            error_msg = "The URL does not point to a valid PDF file."
            logging.warning(f"URL does not appear to be a PDF: {url}")
            return (None, error_msg)
            
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code
        if status == 404:
            error_msg = "PDF not found. This paper may not have a PDF available."
        elif status == 403:
            error_msg = "Access denied. The PDF may be restricted or unavailable."
        elif status >= 500:
            error_msg = f"Server error ({status}). The paper repository is temporarily down."
        else:
            error_msg = f"Failed to access PDF (HTTP {status})."
        logging.error(f"HTTP error downloading PDF from {url}: {str(e)}")
        return (None, error_msg)
    except Exception as e:
        logging.error(f"Error downloading PDF from {url}: {str(e)}")
        return (None, f"Failed to download PDF: {str(e)}")


def extract_text_from_pdf(pdf_content: bytes, max_pages: Optional[int] = None) -> str:
    """
    Extract text from PDF using PyMuPDF (fitz).
    """
    try:
        # Open PDF from bytes
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        
        text_parts = []
        total_pages = len(doc)
        pages_to_process = min(max_pages, total_pages) if max_pages else total_pages
        
        for page_num in range(pages_to_process):
            page = doc[page_num]
            text = page.get_text()
            if text:
                text_parts.append(text)
        
        doc.close()
        
        # Join all text
        full_text = "\n\n".join(text_parts)
        
        # Clean up the text
        cleaned_text = clean_extracted_text(full_text, preserve_all=True)
        
        logging.info(f"Extracted text: {len(cleaned_text)} characters")
        return cleaned_text
        
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {str(e)}")
        return ""


def clean_extracted_text(text: str, preserve_all: bool = True) -> str:
    """
    Clean extracted text.
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {3,}', ' ', text)
    
    if not preserve_all:
        lines = text.split('\n')
        cleaned_lines = []
        skip = False
        for line in lines:
            line_l = line.lower().strip()
            if any(p in line_l for p in ['references', 'bibliography']):
                if len(line.strip()) < 50: skip = True; continue
            if not skip: cleaned_lines.append(line)
        text = '\n'.join(cleaned_lines)
    
    return text.strip()


def get_pdf_text_from_url(pdf_url: str, max_pages: Optional[int] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Download PDF from URL and extract text.
    """
    pdf_content, download_error = download_pdf(pdf_url)
    if pdf_content is None:
        return (None, download_error)
    
    extracted_text = extract_text_from_pdf(pdf_content, max_pages=max_pages)
    if not extracted_text or len(extracted_text.strip()) < 100:
        return (None, "Failed to extract sufficient text from PDF.")
    
    return (extracted_text, None)


def extract_structured_text_from_pdf(pdf_content: bytes, max_pages: Optional[int] = None) -> list:
    """
    Simplified structured extraction to ensure it doesn't fail.
    """
    try:
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        total_pages = len(doc)
        pages_to_process = min(max_pages, total_pages) if max_pages else total_pages
        
        structured_blocks = []
        for page_num in range(pages_to_process):
            page = doc[page_num]
            blocks = page.get_text("blocks")
            for b in blocks:
                text = b[4].strip()
                if text:
                    # Simple classification: caps + short = heading, else body
                    btype = "body"
                    if text.isupper() and len(text) < 100: btype = "heading"
                    structured_blocks.append({"type": btype, "text": text})
        
        doc.close()
        return structured_blocks
    except:
        return []


def get_structured_pdf_text_from_url(pdf_url: str, max_pages: Optional[int] = None) -> Tuple[Optional[list], Optional[str]]:
    pdf_content, download_error = download_pdf(pdf_url)
    if pdf_content is None: return (None, download_error)
    blocks = extract_structured_text_from_pdf(pdf_content, max_pages=max_pages)
    return (blocks, None)
