"""
PDF Service
Handles downloading and text extraction from PDFs using PyMuPDF.
"""
import logging
import requests
import time
from typing import Optional, Tuple
from collections import OrderedDict
import fitz  # PyMuPDF


# ---- In-memory PDF text cache (LRU with TTL) ----
_PDF_TEXT_CACHE: OrderedDict = OrderedDict()  # key: url -> (text, timestamp)
_PDF_CACHE_MAX_SIZE = 50  # Max cached PDFs
_PDF_CACHE_TTL = 3600     # 1 hour TTL


def _get_cached_text(url: str) -> Optional[str]:
    """Get cached PDF text if it exists and hasn't expired."""
    if url in _PDF_TEXT_CACHE:
        text, ts = _PDF_TEXT_CACHE[url]
        if time.time() - ts < _PDF_CACHE_TTL:
            _PDF_TEXT_CACHE.move_to_end(url)  # Mark as recently used
            logging.info(f"PDF cache HIT for: {url[:80]}...")
            return text
        else:
            del _PDF_TEXT_CACHE[url]  # Expired
            logging.info(f"PDF cache EXPIRED for: {url[:80]}...")
    return None


def _set_cached_text(url: str, text: str):
    """Cache extracted PDF text with LRU eviction."""
    _PDF_TEXT_CACHE[url] = (text, time.time())
    _PDF_TEXT_CACHE.move_to_end(url)
    # Evict oldest if over capacity
    while len(_PDF_TEXT_CACHE) > _PDF_CACHE_MAX_SIZE:
        evicted_url, _ = _PDF_TEXT_CACHE.popitem(last=False)
        logging.info(f"PDF cache EVICTED: {evicted_url[:80]}...")


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
    Download PDF from URL and extract text. Uses in-memory cache to avoid
    re-downloading the same PDF (e.g., when user summarizes then asks questions).
    
    Args:
        pdf_url: URL to PDF file
        max_pages: Maximum number of pages to process
    
    Returns:
        Tuple of (extracted text, error_message)
        If successful: (text, None)
        If failed: (None, error_message)
    """
    # Check cache first (only for full extraction, not partial)
    if max_pages is None:
        cached = _get_cached_text(pdf_url)
        if cached is not None:
            return (cached, None)
    
    pdf_content, download_error = download_pdf(pdf_url)
    if pdf_content is None:
        return (None, download_error)
    
    extracted_text = extract_text_from_pdf(pdf_content, max_pages=max_pages)
    if not extracted_text or len(extracted_text.strip()) < 100:
        return (None, "Failed to extract sufficient text from PDF. The PDF may be image-based, corrupted, or contain only images.")
    
    # Cache the result for future use (only full extractions)
    if max_pages is None:
        _set_cached_text(pdf_url, extracted_text)
    
    return (extracted_text, None)


def extract_structured_text_from_pdf(pdf_content: bytes, max_pages: Optional[int] = None) -> list:
    """
    Extract structured text from PDF using PyMuPDF's dict mode.
    Analyzes font sizes and styles to classify blocks as heading, subheading, or body.
    
    Args:
        pdf_content: PDF file content as bytes
        max_pages: Maximum number of pages to process (None for all)
    
    Returns:
        List of structured blocks: [{ "type": "heading"|"subheading"|"body", "text": "..." }]
    """
    import re
    from statistics import median
    
    try:
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        total_pages = len(doc)
        pages_to_process = min(max_pages, total_pages) if max_pages else total_pages
        
        # First pass: collect all font sizes to determine the median (body) font size
        all_font_sizes = []
        raw_blocks = []
        
        for page_num in range(pages_to_process):
            page = doc[page_num]
            page_dict = page.get_text("dict", sort=True)
            
            for block in page_dict.get("blocks", []):
                if block.get("type") != 0:  # Skip image blocks
                    continue
                
                block_spans = []
                block_text_parts = []
                
                for line in block.get("lines", []):
                    line_text_parts = []
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if not text:
                            continue
                        font_size = span.get("size", 10)
                        font_name = span.get("font", "").lower()
                        is_bold = "bold" in font_name or "heavy" in font_name or "black" in font_name
                        
                        all_font_sizes.append(font_size)
                        block_spans.append({
                            "size": font_size,
                            "bold": is_bold,
                            "font": font_name,
                        })
                        line_text_parts.append(text)
                    
                    if line_text_parts:
                        block_text_parts.append(" ".join(line_text_parts))
                
                if block_text_parts and block_spans:
                    full_text = "\n".join(block_text_parts)
                    # Use the dominant (most common) font size for the block
                    avg_size = sum(s["size"] for s in block_spans) / len(block_spans)
                    any_bold = any(s["bold"] for s in block_spans)
                    all_bold = all(s["bold"] for s in block_spans)
                    
                    raw_blocks.append({
                        "text": full_text,
                        "avg_size": avg_size,
                        "any_bold": any_bold,
                        "all_bold": all_bold,
                        "span_count": len(block_spans),
                    })
        
        doc.close()
        
        if not raw_blocks or not all_font_sizes:
            return []
        
        # Determine the median font size (this is the body text size)
        median_size = median(all_font_sizes)
        
        # Classify blocks
        structured_blocks = []
        
        for block in raw_blocks:
            text = block["text"].strip()
            if not text:
                continue
            
            # Clean excessive whitespace
            text = re.sub(r'\n{3,}', '\n\n', text)
            text = re.sub(r' {3,}', ' ', text)
            
            avg_size = block["avg_size"]
            all_bold = block["all_bold"]
            any_bold = block["any_bold"]
            
            # Classification heuristics
            # --- New Score-Based Classification Logic ---
            
            # Base score
            score = 0
            is_header_candidate = False
            
            # Feature 1: Font Size (weighted, but not the only factor)
            size_ratio = avg_size / median_size if median_size > 0 else 1.0
            if size_ratio > 1.4: score += 4      # Significantly larger
            elif size_ratio > 1.15: score += 2   # Moderately larger
            elif size_ratio > 1.05: score += 1   # Slightly larger
            
            # Feature 2: Font Weight & Style
            if all_bold: score += 3
            elif any_bold: score += 1
            
            # Feature 3: Casing (All Caps is a strong header signal)
            if text.isupper() and len(text) > 4: score += 2
             
            # Feature 4: Length (Headers are rarely long)
            if len(text) < 50: score += 1
            if len(text) > 150: score -= 5       # Too long to be a header
            if len(text) > 300: score -= 10      # Definitely body text
            
            # Feature 5: Structural Patterns (Numbering: "1.", "2.1", "IV.")
            # Matches: "1. Introduction", "2.1 Methods", "IV. Analysis"
            if re.match(r'^(?:\d+\.|[IVX]+\.)\s+', text): score += 5
            if re.match(r'^(?:\d+\.\d+)\s+', text): score += 4
            
            # Feature 6: Semantic Key Terms (The "Golden" Signal)
            # Common academic section headers
            HEADER_KEYWORDS = [
                'abstract', 'introduction', 'related work', 'background', 
                'literature review', 'methodology', 'methods', 'experimental setup',
                'results', 'analysis', 'discussion', 'conclusion', 'conclusions',
                'references', 'bibliography', 'acknowledgments', 'acknowledgements',
                'appendix', 'data availability', 'conflict of interest'
            ]
            
            clean_lower = text.lower().strip()
            # Exact match or "1. Introduction" format
            if any(k == clean_lower for k in HEADER_KEYWORDS):
                score += 10
            elif any(clean_lower.endswith(k) and len(clean_lower) < 30 for k in HEADER_KEYWORDS):
                score += 8  # e.g. "1. Introduction"
                
            # Feature 7: Negative Keywords (Captions, etc.)
            # "Figure 1", "Table 2" should NOT be headings
            if re.match(r'^(figure|fig\.|table|chart|graph)\s+\d+', clean_lower):
                score -= 10
                is_header_candidate = False
                
            # Feature 8: Garbage Collection (Page Numbers, etc.)
            # If text has NO letters, it's likely a page number or symbol -> NOT a header
            if not re.search(r'[a-zA-Z]', text):
                score -= 50
                is_header_candidate = False
            
            # If text is purely numeric (e.g., "13") -> NOT a header
            if text.strip().isdigit():
                score -= 50
                is_header_candidate = False
                
            # If text is very short (< 3 chars) and NOT a known Roman numeral -> NOT a header
            if len(text) < 3 and not re.match(r'^(I|V|X|A|B|C)\.?$', text):
                score -= 20
            
            # Determine Block Type based on Score
            if score >= 6:
                block_type = "heading"
            elif score >= 3:
                block_type = "subheading"
            else:
                block_type = "body"
            
            # Structure Correction: 
            # If a strict "body" block follows another "body" block and looks like a continuation, merge them.
            if (structured_blocks 
                and structured_blocks[-1]["type"] == "body" 
                and block_type == "body"
                # Check if previous block didn't end with strong punctuation
                and not re.search(r'[.!?:]$', structured_blocks[-1]["text"].strip())
                # And valid length
                and len(structured_blocks[-1]["text"]) < 1000):
                
                structured_blocks[-1]["text"] += " " + text
            else:
                structured_blocks.append({
                    "type": block_type,
                    "text": text,
                })
        
        # --- Post-Processing: Filtering Orphan Headers (Graphics/Charts) ---
        # Rule: A Header is valid ONLY IF it is followed by a Body block of sufficient length
        #       OR another Header. If followed by nothing or short text, it's likely a chart label.
        
        final_blocks = []
        for i, block in enumerate(structured_blocks):
            if block["type"] in ["heading", "subheading"]:
                # 1. Always keep "Golden Headers" (Introduction, Methods, etc.)
                is_golden = False
                clean_lower = block["text"].lower().strip()
                if any(k in clean_lower for k in HEADER_KEYWORDS):
                    is_golden = True
                
                if is_golden:
                    final_blocks.append(block)
                    continue
                
                # 2. Check Context
                # Look ahead for a "validating" neighbor
                has_content_follower = False
                
                # Check next 3 blocks (to skip over small captions/noise)
                for j in range(1, 4):
                    if i + j >= len(structured_blocks):
                        break
                    
                    follower = structured_blocks[i+j]
                    
                    # If followed by another header, we are part of a structure -> valid
                    if follower["type"] in ["heading", "subheading"]:
                        has_content_follower = True
                        break
                    
                    # If followed by substantial body text -> valid
                    # "Substantial" = > 60 chars AND not a Figure caption
                    if follower["type"] == "body":
                        follower_text_lower = follower["text"].lower().strip()
                        if (len(follower["text"]) > 60 
                            and not follower_text_lower.startswith(('figure', 'table', 'chart', 'graph'))):
                            has_content_follower = True
                            break
                
                if has_content_follower:
                    final_blocks.append(block)
                else:
                    # Downgrade to body (it's likely a chart label or isolated text)
                    if final_blocks and final_blocks[-1]["type"] == "body":
                        final_blocks[-1]["text"] += " " + block["text"]
                    else:
                        block["type"] = "body"
                        final_blocks.append(block)
            else:
                final_blocks.append(block)
        
        structured_blocks = final_blocks
        
        logging.info(f"Extracted {len(structured_blocks)} structured blocks from {pages_to_process} pages")
        return structured_blocks
        
    except Exception as e:
        logging.error(f"Error extracting structured text from PDF: {str(e)}")
        return []


def get_structured_pdf_text_from_url(pdf_url: str, max_pages: Optional[int] = None) -> Tuple[Optional[list], Optional[str]]:
    """
    Download PDF from URL and extract structured text with formatting metadata.
    
    Args:
        pdf_url: URL to PDF file
        max_pages: Maximum number of pages to process
    
    Returns:
        Tuple of (structured blocks list, error_message)
        If successful: (blocks, None)
        If failed: (None, error_message)
    """
    pdf_content, download_error = download_pdf(pdf_url)
    if pdf_content is None:
        return (None, download_error)
    
    structured_blocks = extract_structured_text_from_pdf(pdf_content, max_pages=max_pages)
    if not structured_blocks:
        return (None, "Failed to extract structured text from PDF. The PDF may be image-based or corrupted.")
    
    return (structured_blocks, None)
