"""Gemini API client wrapper."""

import json
from google import genai
from app.config import get_settings

_client = None


def get_gemini_client():
    """Get configured Gemini client instance."""
    global _client
    
    if _client is None:
        settings = get_settings()
        _client = genai.Client(api_key=settings.gemini_api_key)
    
    return _client


async def generate_json(prompt: str, max_retries: int = 3) -> dict | list:
    """
    Generate JSON response from Gemini.
    
    Includes retry logic for parsing failures.
    """
    client = get_gemini_client()
    
    # Add JSON instruction to prompt
    full_prompt = f"""{prompt}

IMPORTANT: Respond ONLY with valid JSON. No markdown, no explanation, just the JSON object/array."""
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=full_prompt
            )
            text = response.text.strip()
            
            # Remove markdown code blocks if present
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            return json.loads(text)
            
        except json.JSONDecodeError as e:
            if attempt < max_retries - 1:
                continue
            raise ValueError(f"Failed to parse Gemini response as JSON after {max_retries} attempts: {e}")
        except Exception as e:
            if attempt < max_retries - 1:
                continue
            raise


async def generate_text(prompt: str) -> str:
    """Generate text response from Gemini."""
    client = get_gemini_client()
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text
