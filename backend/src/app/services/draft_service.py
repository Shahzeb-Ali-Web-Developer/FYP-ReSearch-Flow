"""
Draft Service
Generates structured research drafts from papers using OpenAI GPT-4o.
Includes GPT-4o Vision for analyzing figures/charts extracted from PDFs.
"""
import logging
import json
import time
import requests
from typing import Dict, List, Optional
from ..core.config import settings

logger = logging.getLogger(__name__)

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


def _get_llm_config():
    """Get LLM API URL, key, and extra headers based on available config."""
    if settings.OPENAI_API_KEY:
        return OPENAI_API_URL, settings.OPENAI_API_KEY, {}
    elif getattr(settings, "OPENROUTER_API_KEY", None):
        return (
            OPENROUTER_API_URL,
            settings.OPENROUTER_API_KEY,
            {
                "HTTP-Referer": "https://fyp-re-search-flow.local",
                "X-Title": "ReSearch Flow",
            },
        )
    else:
        raise ValueError("No LLM API key configured (OPENAI_API_KEY or OPENROUTER_API_KEY)")


def analyze_figure(image_base64: str, mime_type: str, caption_hint: str = "", model: str = "gpt-4o") -> Optional[Dict]:
    """
    Analyze a single figure/chart using GPT-4o Vision.

    Args:
        image_base64: Base64-encoded image
        mime_type: MIME type (e.g. "image/png")
        caption_hint: Optional caption text found near the figure
        model: OpenAI model to use

    Returns:
        Dict with keys: description, data_insights, chart_type
    """
    api_url, api_key, extra_headers = _get_llm_config()

    caption_context = f"\nCaption found near this figure: \"{caption_hint}\"" if caption_hint else ""

    messages = [
        {
            "role": "system",
            "content": "You are an expert research analyst. Analyze figures and charts from academic papers accurately and concisely."
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"""Analyze this figure from a research paper. Provide a JSON response with:
{{
  "chart_type": "type of visualization (e.g., bar chart, line graph, scatter plot, diagram, table, photograph, etc.)",
  "description": "Clear description of what the figure shows (2-3 sentences)",
  "data_insights": "Key data points, trends, or takeaways from this figure (2-3 sentences)"
}}{caption_context}"""
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_base64}",
                        "detail": "low"  # Use low detail to save tokens
                    }
                }
            ]
        }
    ]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    headers.update(extra_headers)

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 500,
        "response_format": {"type": "json_object"},
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()

        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            analysis = json.loads(content)
            return {
                "chart_type": analysis.get("chart_type", "Unknown"),
                "description": analysis.get("description", ""),
                "data_insights": analysis.get("data_insights", ""),
            }
    except Exception as e:
        logger.error(f"Figure analysis failed: {e}")

    return None


def generate_draft(
    paper_text: str,
    figure_analyses: List[Dict],
    title: str = "",
    authors: str = "",
    abstract: str = "",
    model: str = "gpt-4o",
) -> Optional[Dict]:
    """
    Generate a structured research draft from paper text and figure analyses.

    Args:
        paper_text: Full extracted text of the paper
        figure_analyses: List of figure analysis dicts from analyze_figure()
        title: Paper title
        authors: Paper authors
        abstract: Paper abstract
        model: OpenAI model to use

    Returns:
        Dict with draft sections, or None on error
    """
    api_url, api_key, extra_headers = _get_llm_config()

    if not paper_text or len(paper_text.strip()) < 100:
        logger.warning("Paper text too short for draft generation")
        return None

    # Strip references section to save tokens
    import re
    ref_match = re.search(
        r'\n\s*(?:References|REFERENCES|Bibliography|BIBLIOGRAPHY)\s*\n', paper_text
    )
    if ref_match:
        paper_text = paper_text[:ref_match.start()]

    # Truncate if too long
    max_chars = 90000
    if len(paper_text) > max_chars:
        paper_text = paper_text[:max_chars] + "\n\n[Content truncated...]"

    # Build figure context for the prompt
    figure_context = ""
    if figure_analyses:
        figure_context = "\n\n--- FIGURE ANALYSES ---\n"
        for i, fig in enumerate(figure_analyses, 1):
            figure_context += f"\nFigure {i} (Page {fig.get('page_number', '?')}, {fig.get('chart_type', 'Unknown')}):\n"
            figure_context += f"  Description: {fig.get('description', 'N/A')}\n"
            figure_context += f"  Key Insights: {fig.get('data_insights', 'N/A')}\n"

    # Build metadata context
    meta_context = ""
    if title:
        meta_context += f"Title: {title}\n"
    if authors:
        meta_context += f"Authors: {authors}\n"
    if abstract:
        meta_context += f"Abstract: {abstract}\n"

    prompt = f"""You are an expert academic writer. Based on the following research paper content and figure analyses, generate a structured research draft.

{meta_context}

--- PAPER CONTENT ---
{paper_text}
{figure_context}

Generate a research draft in the following JSON format:
{{
  "introduction": "A well-written introduction covering the background, significance, and objectives of this research (3-5 paragraphs)",
  "literature_context": "How this paper fits within the broader research landscape, key related work referenced, and gaps addressed (2-4 paragraphs)",
  "methodology_overview": "Detailed analysis of the methods, experimental design, datasets, and tools used in this research (2-4 paragraphs)",
  "key_analysis": "Critical analysis and discussion of the main findings, results, and their significance. Reference relevant figures where applicable (3-5 paragraphs)",
  "figure_discussions": "Detailed discussion of the visual data presented in the paper's figures, what they reveal, and their implications (1-3 paragraphs, or 'No figures available' if none)",
  "conclusion": "Synthesis of the paper's contributions, limitations, and potential future research directions (2-3 paragraphs)"
}}

IMPORTANT GUIDELINES:
- Write in formal academic English
- Reference specific data, metrics, and results from the paper
- When discussing figures, reference the figure analyses provided
- Be thorough but concise — each section should be substantive
- The draft should read as a cohesive academic document"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    headers.update(extra_headers)

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are an expert academic writer specializing in creating comprehensive research drafts. Write in clear, formal academic prose.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 4000,
        "response_format": {"type": "json_object"},
    }

    try:
        logger.info(f"Generating draft via {api_url} with model {model}")
        response = requests.post(api_url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        result = response.json()

        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            draft = json.loads(content)

            # Validate required sections
            required = ["introduction", "methodology_overview", "key_analysis", "conclusion"]
            for section in required:
                if section not in draft or not draft[section]:
                    draft[section] = f"Unable to generate {section.replace('_', ' ')}. Please try again."

            # Optional sections fallback
            draft.setdefault("literature_context", "")
            draft.setdefault("figure_discussions", "No figures available" if not figure_analyses else "")

            logger.info("Successfully generated research draft")
            return draft

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse draft JSON: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Draft generation API request failed: {e}")
    except Exception as e:
        logger.error(f"Draft generation error: {e}", exc_info=True)

    return None
