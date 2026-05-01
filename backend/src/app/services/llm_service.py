"""
LLM Service
Handles communication with OpenRouter API for LLM-based summarization.
"""
import logging
import json
import requests
from typing import Dict, Optional
from ..core.config import settings

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


def summarize_with_llm(text: str, model: str = "gpt-4o") -> Optional[Dict[str, str]]:
    """
    Summarize a research paper using OpenAI API.
    
    Args:
        text: Full text of the paper to summarize
        model: Model to use (default: gpt-4o-mini for speed and cost efficiency)
    
    Returns:
        Dictionary with structured summary sections, or None if error
    """
    # Decide which LLM provider to use: OpenAI or OpenRouter
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    extra_headers: Dict[str, str] = {}

    if settings.OPENAI_API_KEY:
        api_url = OPENAI_API_URL
        api_key = settings.OPENAI_API_KEY
    elif getattr(settings, "OPENROUTER_API_KEY", None):
        api_url = OPENROUTER_API_URL
        api_key = settings.OPENROUTER_API_KEY  # type: ignore[attr-defined]
        # Recommended headers for OpenRouter (non‑critical if left as defaults)
        extra_headers = {
            "HTTP-Referer": "https://fyp-re-search-flow.local",
            "X-Title": "ReSearch Flow",
        }
    else:
        logging.error("No LLM API key configured (OPENAI_API_KEY or OPENROUTER_API_KEY)")
        return None
    
    if not text or len(text.strip()) < 100:
        logging.warning("Text too short for summarization")
        return None
    
    try:
        # Strip references/bibliography section — it adds tokens but no value for summarization
        import re
        ref_pattern = r'\n\s*(?:References|REFERENCES|Bibliography|BIBLIOGRAPHY|Works Cited|WORKS CITED)\s*\n'
        ref_match = re.search(ref_pattern, text)
        if ref_match:
            original_len = len(text)
            text = text[:ref_match.start()]
            logging.info(f"Stripped references section: {original_len} -> {len(text)} chars (saved {original_len - len(text)} chars)")
        
        # Truncate text if still too long (GPT-4o-mini has 128K context window)
        # Keep first ~100000 characters to leave room for prompt and response
        max_chars = 100000
        if len(text) > max_chars:
            logging.info(f"Text too long ({len(text)} chars), truncating to {max_chars} chars")
            text = text[:max_chars] + "\n\n[Content truncated for summarization...]"
        
        # Create a more detailed and structured prompt
        prompt = f"""You are an expert academic researcher. Analyze the following research paper and provide a detailed, structured summary.

IMPORTANT: Provide your response EXACTLY in this JSON format:
{{
  "problem_statement": "A clear description of the research problem or question addressed (2-4 sentences)",
  "methodology": "Detailed description of the methods, approaches, techniques, or frameworks used (3-5 sentences)",
  "key_findings": "The main results, discoveries, or findings from the research (3-6 sentences)",
  "conclusion": "The key conclusions, implications, or contributions of the research (2-4 sentences)"
}}

Research Paper Content:
{text}

Now provide the JSON-formatted summary:"""

        # Make request to chosen LLM API
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        headers.update(extra_headers)
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert academic researcher. Summarize research papers clearly and accurately."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.2,  # Lower temperature for more focused summaries
            "max_tokens": 2000,  # Allow longer responses for detailed summaries
            "response_format": {"type": "json_object"}  # Request JSON format
        }
        
        logging.info(f"Calling LLM API at {api_url} with model: {model}")
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)  # type: ignore[arg-type]
        response.raise_for_status()
        
        result = response.json()
        
        # Extract the summary text from response
        if "choices" in result and len(result["choices"]) > 0:
            summary_text = result["choices"][0]["message"]["content"]
            
            # Try to parse as JSON first
            try:
                summary_json = json.loads(summary_text)
                # Validate structure
                if isinstance(summary_json, dict):
                    summary = {
                        "problem_statement": summary_json.get("problem_statement", "").strip(),
                        "methodology": summary_json.get("methodology", "").strip(),
                        "key_findings": summary_json.get("key_findings", "").strip(),
                        "conclusion": summary_json.get("conclusion", "").strip()
                    }
                    # Validate all fields are present
                    if all(v for v in summary.values()):
                        logging.info("Successfully generated LLM summary (JSON format)")
                        return summary
                    else:
                        logging.warning("LLM response missing some fields, attempting text parsing")
            except json.JSONDecodeError:
                logging.warning("LLM response not in JSON format, attempting text parsing")
            
            # Fallback to text parsing if JSON parsing fails
            summary = _parse_llm_summary(summary_text)
            
            logging.info("Successfully generated LLM summary")
            return summary
        else:
            logging.error(f"Unexpected API response format: {result}")
            return None
            
    except requests.exceptions.RequestException as e:
        logging.error(f"OpenAI API request failed: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Error in LLM summarization: {str(e)}", exc_info=True)
        return None


def _parse_llm_summary(summary_text: str) -> Dict[str, str]:
    """
    Parse the LLM response into structured sections.
    
    Args:
        summary_text: Raw response text from LLM
    
    Returns:
        Dictionary with problem_statement, methodology, key_findings, conclusion
    """
    import re
    
    summary = {
        "problem_statement": "",
        "methodology": "",
        "key_findings": "",
        "conclusion": ""
    }
    
    # Try JSON parsing first (in case it's JSON but not properly formatted)
    try:
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', summary_text, re.DOTALL)
        if json_match:
            summary_json = json.loads(json_match.group(1))
            if isinstance(summary_json, dict):
                summary = {
                    "problem_statement": str(summary_json.get("problem_statement", "")).strip(),
                    "methodology": str(summary_json.get("methodology", "")).strip(),
                    "key_findings": str(summary_json.get("key_findings", "")).strip(),
                    "conclusion": str(summary_json.get("conclusion", "")).strip()
                }
                if all(v for v in summary.values()):
                    return summary
    except:
        pass
    
    # Try to extract sections based on improved patterns
    patterns = {
        "problem_statement": [
            r'(?:problem\s+statement|problem|research\s+question)[:\-]?\s*(.+?)(?=\n\s*(?:methodology|method|approach|key\s+findings|2\.|conclusion|$))',
            r'"problem_statement"[:\s]*"([^"]+)"',
            r'problem_statement["\']?\s*[:=]\s*["\']?([^"\']+)',
            r'1[\.\)]\s*problem[:\-]?\s*(.+?)(?=\n\s*2[\.\)])',
        ],
        "methodology": [
            r'(?:methodology|method|approach|methods)[:\-]?\s*(.+?)(?=\n\s*(?:key\s+findings|results|findings|3\.|conclusion|$))',
            r'"methodology"[:\s]*"([^"]+)"',
            r'methodology["\']?\s*[:=]\s*["\']?([^"\']+)',
            r'2[\.\)]\s*method[:\-]?\s*(.+?)(?=\n\s*3[\.\)])',
        ],
        "key_findings": [
            r'(?:key\s+findings|findings|results|main\s+results)[:\-]?\s*(.+?)(?=\n\s*(?:conclusion|implications|4\.|$))',
            r'"key_findings"[:\s]*"([^"]+)"',
            r'key_findings["\']?\s*[:=]\s*["\']?([^"\']+)',
            r'3[\.\)]\s*findings[:\-]?\s*(.+?)(?=\n\s*4[\.\)])',
        ],
        "conclusion": [
            r'(?:conclusion|conclusions|summary)[:\-]?\s*(.+?)(?=\n\s*$)',
            r'"conclusion"[:\s]*"([^"]+)"',
            r'conclusion["\']?\s*[:=]\s*["\']?([^"\']+)',
            r'4[\.\)]\s*conclusion[:\-]?\s*(.+?)$',
        ]
    }
    
    for section, section_patterns in patterns.items():
        for pattern in section_patterns:
            match = re.search(pattern, summary_text, re.IGNORECASE | re.DOTALL | re.MULTILINE)
            if match:
                extracted = match.group(1).strip()
                # Clean up extracted text
                extracted = re.sub(r'^["\']|["\']$', '', extracted)  # Remove quotes
                extracted = re.sub(r'\s+', ' ', extracted)  # Normalize whitespace
                if len(extracted) > 20:  # Only use if meaningful
                    summary[section] = extracted
                    break
    
    # Fallback: if sections are empty, try splitting by paragraphs
    if not all(v for v in summary.values()):
        paragraphs = [p.strip() for p in summary_text.split("\n\n") if p.strip() and len(p.strip()) > 30]
        if len(paragraphs) >= 4:
            summary["problem_statement"] = paragraphs[0] if not summary["problem_statement"] else summary["problem_statement"]
            summary["methodology"] = paragraphs[1] if not summary["methodology"] else summary["methodology"]
            summary["key_findings"] = paragraphs[2] if not summary["key_findings"] else summary["key_findings"]
            summary["conclusion"] = paragraphs[3] if not summary["conclusion"] else summary["conclusion"]
    
    # Final cleanup - ensure all fields have content
    for key in summary:
        summary[key] = summary[key].strip()
        if not summary[key] or len(summary[key]) < 10:
            summary[key] = f"Unable to extract {key.replace('_', ' ')} from the summary. Please try again."
    
    return summary


def ask_question_with_llm(text: str, question: str, history: list = None, model: str = "gpt-4o") -> Optional[str]:
    """
    Ask a question about a research paper using LLM.
    
    Args:
        text: Full text of the paper
        question: User's question
        history: Conversation history list of dicts [{'role': 'user', 'content': '...'}, ...]
        model: Model to use
    
    Returns:
        String containing the answer, or None if error
    """
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    extra_headers: Dict[str, str] = {}

    if settings.OPENAI_API_KEY:
        api_url = OPENAI_API_URL
        api_key = settings.OPENAI_API_KEY
    elif getattr(settings, "OPENROUTER_API_KEY", None):
        api_url = OPENROUTER_API_URL
        api_key = settings.OPENROUTER_API_KEY  # type: ignore[attr-defined]
        extra_headers = {
            "HTTP-Referer": "https://fyp-re-search-flow.local",
            "X-Title": "ReSearch Flow",
        }
    else:
        logging.error("No LLM API key configured")
        return None
        
    if not text or len(text.strip()) < 100:
        logging.warning("Text too short to answer questions")
        return None
        
    try:
        max_chars = 100000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[Content truncated...]"
            
        system_prompt = f"""You are an expert academic researcher. Answer the user's question based ONLY on the provided research paper content.
If the answer is not in the paper, clearly state that you cannot find the answer in the provided text.

Research Paper Content:
{text}
"""
        messages = [{"role": "system", "content": system_prompt}]
        
        if history:
            messages.extend(history)
            
        messages.append({"role": "user", "content": question})
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        headers.update(extra_headers)
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1000
        }
        
        logging.info(f"Calling LLM API to answer question with model: {model}")
        response = requests.post(api_url, headers=headers, json=payload, timeout=60) # type: ignore[arg-type]
        response.raise_for_status()
        
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            answer = result["choices"][0]["message"]["content"]
            return answer
        else:
            logging.error(f"Unexpected API response format: {result}")
            return None
            
    except Exception as e:
        logging.error(f"Error in LLM answering: {str(e)}", exc_info=True)
        return None


