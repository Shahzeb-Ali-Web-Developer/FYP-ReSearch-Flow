"""
PubMed Central (PMC) API Service
Handles queries to the NCBI E-utilities API for PMC articles.

PDF Download Strategy:
  PMC's direct PDF URLs (pmc.ncbi.nlm.nih.gov/articles/PMC.../pdf/) are protected
  by Cloudflare bot-detection and cannot be fetched programmatically.
  Instead, we fetch the article's full XML via E-utilities (no bot protection),
  parse out all sections, and render a clean PDF locally using reportlab.
  Call `download_pmc_as_pdf(pmc_id, output_path)` to get a real PDF file.
"""
import io
import logging
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

PMC_EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PMC_BASE_URL = "https://pmc.ncbi.nlm.nih.gov/articles/"


def get_pmc_fulltext_from_xml(pmc_id: str) -> Optional[str]:
    """
    Fetch the full-text of a PMC article directly from E-utilities XML API.
    This bypasses the browser-only PDF URL that requires human verification.
    
    Args:
        pmc_id: The numeric PMC ID (without 'PMC' prefix)
    
    Returns:
        Extracted full-text string, or None if not available
    """
    try:
        clean_id = pmc_id.replace('PMC', '').strip()
        fetch_url = f"{PMC_EUTILS_BASE}/efetch.fcgi"
        params = {
            "db": "pmc",
            "id": clean_id,
            "retmode": "xml",
            "rettype": "full"  # Full article text
        }
        
        response = requests.get(fetch_url, params=params, timeout=60)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        
        # Extract all text from the <body> element of the article
        body = root.find(".//body")
        if body is None:
            logging.warning(f"No <body> element found in PMC XML for {pmc_id}")
            return None
        
        # Walk through all sections and paragraphs to build full text
        text_parts = []
        for section in body.iter():
            if section.tag in ('sec', 'p', 'title'):
                # Get direct text (itertext gets all nested text)
                text = ''.join(section.itertext()).strip()
                if text and section.tag == 'title':
                    text_parts.append(f"\n## {text}\n")
                elif text and section.tag == 'p':
                    text_parts.append(text)
        
        if not text_parts:
            # Fallback: just grab ALL text from body
            all_text = ''.join(body.itertext()).strip()
            if all_text and len(all_text) > 200:
                return all_text
            return None
        
        # Deduplicate (section text includes child paragraph text)
        # Use only paragraph and title-level text
        seen = set()
        unique_parts = []
        for part in text_parts:
            # Use first 100 chars as dedup key to handle slight variations
            key = part[:100].strip()
            if key not in seen:
                seen.add(key)
                unique_parts.append(part)
        
        full_text = '\n\n'.join(unique_parts)
        
        if len(full_text.strip()) < 200:
            logging.warning(f"PMC XML full-text too short for {pmc_id}: {len(full_text)} chars")
            return None
        
        logging.info(f"Successfully extracted {len(full_text)} chars from PMC XML for {pmc_id}")
        return full_text
        
    except Exception as e:
        logging.error(f"Error fetching PMC full-text XML for {pmc_id}: {str(e)}")
        return None



def _build_pmc_styles() -> dict:
    """Build a set of ReportLab paragraph styles for PMC articles."""
    base = getSampleStyleSheet()

    styles = {
        "title": ParagraphStyle(
            "ArticleTitle",
            parent=base["Title"],
            fontSize=18,
            leading=24,
            spaceAfter=8,
            textColor=colors.HexColor("#1a1a2e"),
            alignment=TA_LEFT,
        ),
        "authors": ParagraphStyle(
            "Authors",
            parent=base["Normal"],
            fontSize=10,
            leading=14,
            spaceAfter=4,
            textColor=colors.HexColor("#444444"),
            fontName="Helvetica-Oblique",
        ),
        "meta": ParagraphStyle(
            "Meta",
            parent=base["Normal"],
            fontSize=9,
            leading=13,
            spaceAfter=4,
            textColor=colors.HexColor("#666666"),
        ),
        "abstract_heading": ParagraphStyle(
            "AbstractHeading",
            parent=base["Heading2"],
            fontSize=11,
            leading=15,
            spaceBefore=14,
            spaceAfter=4,
            textColor=colors.HexColor("#1a1a2e"),
            fontName="Helvetica-Bold",
        ),
        "abstract_body": ParagraphStyle(
            "AbstractBody",
            parent=base["Normal"],
            fontSize=10,
            leading=15,
            spaceAfter=6,
            textColor=colors.HexColor("#222222"),
            alignment=TA_JUSTIFY,
            leftIndent=12,
            rightIndent=12,
        ),
        "section_heading": ParagraphStyle(
            "SectionHeading",
            parent=base["Heading2"],
            fontSize=12,
            leading=16,
            spaceBefore=16,
            spaceAfter=6,
            textColor=colors.HexColor("#1a1a2e"),
            fontName="Helvetica-Bold",
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontSize=10,
            leading=15,
            spaceAfter=8,
            textColor=colors.HexColor("#222222"),
            alignment=TA_JUSTIFY,
        ),
        "url": ParagraphStyle(
            "URL",
            parent=base["Normal"],
            fontSize=8,
            leading=12,
            spaceAfter=4,
            textColor=colors.HexColor("#0066cc"),
        ),
    }
    return styles


def _fetch_pmc_article_xml(pmc_id: str) -> Optional[ET.Element]:
    """
    Fetch the full PMC article XML via E-utilities (no bot protection).
    Returns the root XML element, or None on failure.
    """
    clean_id = pmc_id.replace("PMC", "").strip()
    fetch_url = f"{PMC_EUTILS_BASE}/efetch.fcgi"
    params = {"db": "pmc", "id": clean_id, "retmode": "xml", "rettype": "full"}
    try:
        resp = requests.get(fetch_url, params=params, timeout=60)
        resp.raise_for_status()
        return ET.fromstring(resp.content)
    except Exception as e:
        logging.error(f"Failed to fetch PMC XML for {pmc_id}: {e}")
        return None


def _safe_text(elem: Optional[ET.Element]) -> str:
    """Extract all text from an XML element safely."""
    if elem is None:
        return ""
    return "".join(elem.itertext()).strip()


def _escape_xml(text: str) -> str:
    """Escape special XML/HTML characters for ReportLab Paragraph."""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


def _xml_to_story(root: ET.Element, styles: dict) -> list:
    """
    Walk the PMC XML tree and build a ReportLab story (list of Flowables).
    Extracts: title, authors, journal/date, abstract, and all body sections.
    """
    story = []
    article = root.find(".//article")
    if article is None:
        article = root  # fallback

    # ── Title ──────────────────────────────────────────────────────────────
    title_elem = article.find(".//article-title")
    title_text = _escape_xml(_safe_text(title_elem)) or "Untitled Article"
    story.append(Paragraph(title_text, styles["title"]))

    # ── Authors ────────────────────────────────────────────────────────────
    authors = []
    for contrib in article.findall(".//contrib[@contrib-type='author']"):
        given = contrib.findtext(".//given-names", "").strip()
        surname = contrib.findtext(".//surname", "").strip()
        name = f"{given} {surname}".strip()
        if name:
            authors.append(name)
    if authors:
        story.append(Paragraph(_escape_xml(", ".join(authors)), styles["authors"]))

    # ── Journal / Date metadata ────────────────────────────────────────────
    journal = _safe_text(article.find(".//journal-title"))
    pub_date_elem = (
        article.find(".//pub-date[@pub-type='ppub']")
        or article.find(".//pub-date[@pub-type='epub']")
        or article.find(".//pub-date")
    )
    year = pub_date_elem.findtext("year", "") if pub_date_elem is not None else ""
    meta_parts = [p for p in [journal, year] if p]
    if meta_parts:
        story.append(Paragraph(_escape_xml(" | ".join(meta_parts)), styles["meta"]))

    # ── DOI / URL ──────────────────────────────────────────────────────────
    doi_elem = article.find(".//article-id[@pub-id-type='doi']")
    pmc_id_elem = article.find(".//article-id[@pub-id-type='pmc']")
    if doi_elem is not None and doi_elem.text:
        doi_url = doi_elem.text if doi_elem.text.startswith("http") else f"https://doi.org/{doi_elem.text}"
        story.append(Paragraph(f"DOI: {_escape_xml(doi_url)}", styles["url"]))
    if pmc_id_elem is not None and pmc_id_elem.text:
        pmc_url = f"https://pmc.ncbi.nlm.nih.gov/articles/PMC{pmc_id_elem.text}/"
        story.append(Paragraph(f"PMC: {_escape_xml(pmc_url)}", styles["url"]))

    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 10))

    # ── Abstract ───────────────────────────────────────────────────────────
    abstract_elem = article.find(".//abstract")
    if abstract_elem is not None:
        story.append(Paragraph("Abstract", styles["abstract_heading"]))
        # Some abstracts have labelled sections; others are flat paragraphs
        sections = abstract_elem.findall(".//sec")
        if sections:
            for sec in sections:
                sec_title = _safe_text(sec.find("title"))
                if sec_title:
                    story.append(Paragraph(_escape_xml(sec_title), styles["abstract_heading"]))
                for para in sec.findall(".//p"):
                    txt = _escape_xml(_safe_text(para))
                    if txt:
                        story.append(Paragraph(txt, styles["abstract_body"]))
        else:
            for para in abstract_elem.findall(".//p"):
                txt = _escape_xml(_safe_text(para))
                if txt:
                    story.append(Paragraph(txt, styles["abstract_body"]))
            # Fallback if no <p> tags
            if not abstract_elem.findall(".//p"):
                flat = _escape_xml(_safe_text(abstract_elem))
                if flat:
                    story.append(Paragraph(flat, styles["abstract_body"]))

        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dddddd")))

    # ── Body sections ──────────────────────────────────────────────────────
    body = article.find(".//body")
    if body is not None:
        for sec in body.findall("sec"):
            _render_section(sec, story, styles, depth=0)

    # ── Fallback: no body, dump everything ────────────────────────────────
    if body is None:
        all_text = _escape_xml("".join(article.itertext()).strip())
        if all_text:
            story.append(Paragraph(all_text, styles["body"]))

    return story


def _render_section(sec: ET.Element, story: list, styles: dict, depth: int):
    """Recursively render a <sec> element into ReportLab flowables."""
    title_elem = sec.find("title")
    if title_elem is not None:
        title_text = _escape_xml(_safe_text(title_elem))
        if title_text:
            story.append(Paragraph(title_text, styles["section_heading"]))

    for child in sec:
        tag = child.tag
        if tag == "title":
            continue  # already handled above
        elif tag == "p":
            txt = _escape_xml(_safe_text(child))
            if txt:
                story.append(Paragraph(txt, styles["body"]))
        elif tag == "sec":
            _render_section(child, story, styles, depth + 1)
        elif tag in ("fig", "table-wrap"):
            # Add caption if present
            caption = child.find(".//caption/p") or child.find(".//label")
            if caption is not None:
                cap_txt = _escape_xml(_safe_text(caption))
                if cap_txt:
                    caption_style = ParagraphStyle(
                        "Caption", parent=styles["body"],
                        fontSize=9, textColor=colors.HexColor("#555555"),
                        fontName="Helvetica-Oblique", spaceAfter=4,
                    )
                    story.append(Paragraph(f"[Figure/Table: {cap_txt}]", caption_style))
        elif tag == "list":
            for item in child.findall("list-item"):
                item_text = _escape_xml(_safe_text(item))
                if item_text:
                    story.append(Paragraph(f"• {item_text}", styles["body"]))


def download_pmc_as_pdf(pmc_id: str, output_path: str) -> bool:
    """
    Download a PMC article as a PDF by fetching its XML via E-utilities
    (which has no bot protection) and rendering it locally with ReportLab.

    This completely bypasses the Cloudflare/browser-verification wall on
    PMC's direct PDF download URLs.

    Args:
        pmc_id: PMC ID with or without 'PMC' prefix (e.g. 'PMC9876543' or '9876543')
        output_path: File path where the PDF should be saved (e.g. '/tmp/article.pdf')

    Returns:
        True on success, False on failure
    """
    clean_id = pmc_id.replace("PMC", "").strip()
    logging.info(f"Generating PDF for PMC{clean_id} → {output_path}")

    # 1. Fetch XML from E-utilities (always works, no bot protection)
    root = _fetch_pmc_article_xml(clean_id)
    if root is None:
        logging.error(f"Could not fetch XML for PMC{clean_id}")
        return False

    # 2. Build ReportLab styles and story
    try:
        styles = _build_pmc_styles()
        story = _xml_to_story(root, styles)
    except Exception as e:
        logging.error(f"Failed to parse article XML for PMC{clean_id}: {e}")
        return False

    if not story:
        logging.error(f"No content extracted from PMC{clean_id}")
        return False

    # 3. Render to PDF
    try:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            leftMargin=1 * inch,
            rightMargin=1 * inch,
            topMargin=1 * inch,
            bottomMargin=1 * inch,
            title=f"PMC{clean_id}",
            author="PMC E-utilities Export",
        )
        doc.build(story)
        size_kb = Path(output_path).stat().st_size // 1024
        logging.info(f"PDF saved: {output_path} ({size_kb} KB)")
        return True
    except Exception as e:
        logging.error(f"Failed to render PDF for PMC{clean_id}: {e}")
        return False


def get_pmc_pdf_bytes(pmc_id: str) -> Optional[bytes]:
    """
    Like download_pmc_as_pdf() but returns the PDF as bytes instead of
    saving to disk. Useful for streaming the PDF directly to a client.

    Args:
        pmc_id: PMC ID with or without 'PMC' prefix

    Returns:
        PDF bytes on success, or None on failure
    """
    clean_id = pmc_id.replace("PMC", "").strip()
    root = _fetch_pmc_article_xml(clean_id)
    if root is None:
        return None
    try:
        styles = _build_pmc_styles()
        story = _xml_to_story(root, styles)
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=letter,
            leftMargin=1 * inch,
            rightMargin=1 * inch,
            topMargin=1 * inch,
            bottomMargin=1 * inch,
        )
        doc.build(story)
        return buf.getvalue()
    except Exception as e:
        logging.error(f"Failed to generate PDF bytes for PMC{clean_id}: {e}")
        return None


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
        
        # PDF URL - EuropePMC is currently unreliable, using the official PMC PDF endpoint 
        # (Note: direct NCBI PDF downloads may require human verification, but our backend 
        # uses E-utilities XML for full-text extraction to bypass this when summarizing)
        pdf_url = f"https://pmc.ncbi.nlm.nih.gov/articles/PMC{pmc_id}/pdf/"
        
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