"""
PDF Service
Handles downloading and text extraction from PDFs using PyMuPDF.
"""
import logging
import requests
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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
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
        if e.response.status_code == 404:
            error_msg = "PDF not found. This paper may not have a PDF available."
        elif e.response.status_code == 403:
            error_msg = "Access denied. The PDF may be restricted or unavailable."
        else:
            error_msg = f"Failed to access PDF (HTTP {e.response.status_code}). The PDF may not be available."
        logging.error(f"HTTP error downloading PDF from {url}: {str(e)}")
        return (None, error_msg)
    except requests.exceptions.Timeout:
        error_msg = "Request timed out. The PDF server may be slow or unavailable."
        logging.error(f"Timeout downloading PDF from {url}")
        return (None, error_msg)
    except requests.exceptions.ConnectionError:
        error_msg = "Connection error. Unable to reach the PDF server."
        logging.error(f"Connection error downloading PDF from {url}")
        return (None, error_msg)
    except requests.exceptions.RequestException as e:
        error_msg = "Failed to download PDF. The file may not be available."
        logging.error(f"Failed to download PDF from {url}: {str(e)}")
        return (None, error_msg)
    except Exception as e:
        error_msg = "An unexpected error occurred while downloading the PDF."
        logging.error(f"Unexpected error downloading PDF: {str(e)}")
        return (None, error_msg)


def extract_text_from_pdf(pdf_content: bytes, max_pages: Optional[int] = None) -> str:
    """
    Extract text from PDF using PyMuPDF (fitz).
    
    Args:
        pdf_content: PDF file content as bytes
        max_pages: Maximum number of pages to process (None for all)
    
    Returns:
        Extracted text as string
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
        
        # Clean up the text (preserve all content for full extraction)
        cleaned_text = clean_extracted_text(full_text, preserve_all=True)
        
        logging.info(f"Extracted text from {pages_to_process}/{total_pages} pages ({len(cleaned_text)} characters)")
        return cleaned_text
        
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {str(e)}")
        return ""


def clean_extracted_text(text: str, preserve_all: bool = True) -> str:
    """
    Clean extracted text by removing excessive whitespace and normalizing spacing.
    When preserve_all=True, keeps all content including references.
    
    Args:
        text: Raw extracted text
        preserve_all: If True, preserve all content (default: True)
    
    Returns:
        Cleaned text
    """
    import re
    
    if not text:
        return ""
    
    # Remove excessive whitespace (3+ newlines become 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove excessive spaces (3+ spaces become single space)
    text = re.sub(r' {3,}', ' ', text)
    
    # Only skip references if preserve_all is False
    if not preserve_all:
        lines = text.split('\n')
        cleaned_lines = []
        skip_references = False
        
        for line in lines:
            line_lower = line.lower().strip()
            # Skip if we hit a references section (common patterns)
            if any(pattern in line_lower for pattern in ['references', 'bibliography', 'works cited']):
                if len(line.strip()) < 50:  # Likely a section header
                    skip_references = True
                    continue
            
            if not skip_references:
                cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def get_pdf_text_from_url(pdf_url: str, max_pages: Optional[int] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Download PDF from URL and extract text.
    
    Args:
        pdf_url: URL to PDF file
        max_pages: Maximum number of pages to process
    
    Returns:
        Tuple of (extracted text, error_message)
        If successful: (text, None)
        If failed: (None, error_message)
    """
    pdf_content, download_error = download_pdf(pdf_url)
    if pdf_content is None:
        return (None, download_error)
    
    extracted_text = extract_text_from_pdf(pdf_content, max_pages=max_pages)
    if not extracted_text or len(extracted_text.strip()) < 100:
        return (None, "Failed to extract sufficient text from PDF. The PDF may be image-based, corrupted, or contain only images.")
    
    return (extracted_text, None)

