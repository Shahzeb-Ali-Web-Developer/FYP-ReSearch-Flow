"""
Figure Extraction Service
Extracts images/figures from research paper PDFs using PyMuPDF (fitz).
Filters out logos/icons and prepares figures for GPT-4o Vision analysis.
"""
import logging
import base64
import io
import re
from typing import List, Dict, Optional
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

# Minimum dimensions to filter out tiny icons/logos (in pixels)
MIN_WIDTH = 150
MIN_HEIGHT = 150
# Maximum number of figures to extract (to control API costs)
MAX_FIGURES = 8


def extract_figures_from_pdf(pdf_content: bytes, max_figures: int = MAX_FIGURES) -> List[Dict]:
    """
    Extract meaningful figures/images from a PDF.

    Args:
        pdf_content: Raw PDF bytes
        max_figures: Maximum number of figures to extract

    Returns:
        List of dicts with keys:
          - image_base64: Base64-encoded PNG image
          - page_number: 1-indexed page where the image was found
          - width: Image width in pixels
          - height: Image height in pixels
          - caption_hint: Nearby text that might be a caption
    """
    figures = []

    try:
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        total_pages = len(doc)

        for page_num in range(total_pages):
            if len(figures) >= max_figures:
                break

            page = doc[page_num]
            image_list = page.get_images(full=True)

            for img_index, img_info in enumerate(image_list):
                if len(figures) >= max_figures:
                    break

                xref = img_info[0]

                try:
                    base_image = doc.extract_image(xref)
                    if not base_image:
                        continue

                    image_bytes = base_image["image"]
                    width = base_image.get("width", 0)
                    height = base_image.get("height", 0)
                    img_ext = base_image.get("ext", "png")

                    # Filter out small images (logos, icons, decorations)
                    if width < MIN_WIDTH or height < MIN_HEIGHT:
                        continue

                    # Convert to PNG if needed and base64 encode
                    if img_ext.lower() in ("png", "jpeg", "jpg"):
                        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
                        mime_type = f"image/{img_ext.lower()}"
                        if img_ext.lower() == "jpg":
                            mime_type = "image/jpeg"
                    else:
                        # Convert to PNG using fitz Pixmap
                        pix = fitz.Pixmap(doc, xref)
                        if pix.n > 4:  # CMYK — convert to RGB
                            pix = fitz.Pixmap(fitz.csRGB, pix)
                        png_bytes = pix.tobytes("png")
                        image_b64 = base64.b64encode(png_bytes).decode("utf-8")
                        mime_type = "image/png"

                    # Extract nearby text as a caption hint
                    caption_hint = _extract_caption_hint(page, page_num + 1)

                    figures.append({
                        "image_base64": image_b64,
                        "mime_type": mime_type,
                        "page_number": page_num + 1,
                        "width": width,
                        "height": height,
                        "caption_hint": caption_hint,
                    })

                    logger.info(
                        f"Extracted figure from page {page_num + 1}: "
                        f"{width}x{height}px ({img_ext})"
                    )

                except Exception as e:
                    logger.warning(f"Failed to extract image xref={xref} on page {page_num + 1}: {e}")
                    continue

        doc.close()
        logger.info(f"Extracted {len(figures)} figures from {total_pages}-page PDF")

    except Exception as e:
        logger.error(f"Error extracting figures from PDF: {e}")

    return figures


def _extract_caption_hint(page, page_number: int) -> str:
    """
    Try to find figure caption text on the page.
    Looks for text matching patterns like 'Figure 1:', 'Fig. 2:', etc.
    """
    try:
        page_text = page.get_text()
        # Look for figure/fig caption patterns
        caption_patterns = [
            r'(Fig(?:ure)?\.?\s*\d+[.:]\s*[^\n]{10,120})',
            r'(Table\s*\d+[.:]\s*[^\n]{10,120})',
            r'(Chart\s*\d+[.:]\s*[^\n]{10,120})',
        ]

        captions = []
        for pattern in caption_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            captions.extend(matches)

        if captions:
            return captions[0].strip()

    except Exception as e:
        logger.debug(f"Caption extraction failed for page {page_number}: {e}")

    return ""
