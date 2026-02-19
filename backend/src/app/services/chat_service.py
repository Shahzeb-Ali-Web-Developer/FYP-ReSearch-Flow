"""
Chat Service
Handles Q&A conversations about research papers using LLM.
"""
import logging
import json
import requests
from typing import List, Dict, Optional
from ..core.config import settings

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


def ask_about_paper(question: str, paper_text: str, conversation_history: Optional[List[Dict[str, str]]] = None, model: str = "gpt-4o") -> Optional[str]:
    """
    Answer a question about a research paper using LLM with conversation context.
    
    Args:
        question: User's question about the paper
        paper_text: Full extracted text of the paper
        conversation_history: Previous messages in the conversation (optional)
        model: Model to use (default: gpt-4o-mini)
    
    Returns:
        LLM's answer as a string, or None if error
    """
    if not settings.OPENAI_API_KEY:
        logging.error("OPENAI_API_KEY not configured")
        return None
    
    if not question or not question.strip():
        logging.warning("Empty question provided")
        return None
    
    if not paper_text or len(paper_text.strip()) < 100:
        logging.warning("Paper text too short or empty")
        return None
    
    try:
        # Truncate paper text if too long (keep context manageable)
        max_chars = 80000  # Leave room for conversation history
        paper_context = paper_text
        if len(paper_text) > max_chars:
            logging.info(f"Paper text too long ({len(paper_text)} chars), truncating to {max_chars} chars")
            paper_context = paper_text[:max_chars] + "\n\n[Content truncated...]"
        
        # Build conversation messages
        messages = [
            {
                "role": "system",
                "content": """You are an expert research assistant. Your role is to answer questions about research papers clearly and accurately based on the paper content provided. 

Guidelines:
- Answer based ONLY on the information in the provided paper text
- Be specific and cite relevant details from the paper
- If information is not in the paper, say so clearly
- Use clear, academic language
- Be concise but thorough"""
            }
        ]
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add the current paper context and question
        user_message = f"""Paper Content:
{paper_context}

Question: {question.strip()}

Please answer the question based on the paper content above."""
        
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Make request to OpenAI API
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.3,  # Lower temperature for more focused answers
            "max_tokens": 1500  # Sufficient for detailed answers
        }
        
        logging.info(f"Asking question about paper using model: {model}")
        response = requests.post(OPENAI_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        
        # Extract the answer from response
        if "choices" in result and len(result["choices"]) > 0:
            answer = result["choices"][0]["message"]["content"]
            logging.info("Successfully generated answer")
            return answer.strip()
        else:
            logging.error(f"Unexpected API response format: {result}")
            return None
            
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        try:
            error_response = e.response.json()
            error_detail = f" - {error_response}"
        except:
            error_detail = f" - Status: {e.response.status_code}"
        logging.error(f"OpenAI API HTTP error: {str(e)}{error_detail}")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"OpenAI API request failed: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Error in chat service: {str(e)}", exc_info=True)
        return None

