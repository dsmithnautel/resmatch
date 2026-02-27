"""Gemini API client wrapper with rate limiting."""

import asyncio
import json
import re
from typing import Any

from google import genai

from app.config import get_settings

_client: genai.Client | None = None

# Rate limiting: Gemini free tier allows ~15 requests/minute
# We'll be conservative and add delays between requests
RATE_LIMIT_DELAY = 4.0  # seconds between requests
_last_request_time: float = 0.0


def get_gemini_client() -> genai.Client:
    """Get configured Gemini client instance."""
    global _client

    if _client is None:
        settings = get_settings()
        _client = genai.Client(api_key=settings.gemini_api_key)

    return _client


_rate_limit_lock = asyncio.Lock()

async def _rate_limit() -> None:
    """Ensure we don't exceed rate limits by spacing out requests."""
    global _last_request_time
    import time

    async with _rate_limit_lock:
        current_time = time.time()
        time_since_last = current_time - _last_request_time

        if time_since_last < RATE_LIMIT_DELAY:
            wait_time = RATE_LIMIT_DELAY - time_since_last
            await asyncio.sleep(wait_time)

        _last_request_time = time.time()


def _extract_retry_delay(error_message: str) -> float:
    """Extract retry delay from error message if present."""
    # Look for patterns like "retry in 56.602928215s" or "retryDelay: '56s'"
    match = re.search(r"retry.*?(\d+\.?\d*)s", str(error_message), re.IGNORECASE)
    if match:
        return float(match.group(1))
    return 60.0  # Default to 60 seconds if not found


async def generate_json(prompt: str, max_retries: int = 5) -> Any:
    """
    Generate JSON response from Gemini.

    Includes retry logic for:
    - JSON parsing failures
    - Rate limit errors (429) with exponential backoff
    """
    client = get_gemini_client()
    assert client is not None

    # Add JSON instruction to prompt
    full_prompt = f"""{prompt}

IMPORTANT: Respond ONLY with valid JSON. No markdown, no explanation, just the JSON object/array."""

    base_delay = 2.0  # Start with 2 second delay

    for attempt in range(max_retries):
        try:
            await _rate_limit()

            response = await client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=full_prompt,
            )
            if not response.text:
                raise ValueError("Gemini returned an empty response.")
            text = response.text.strip()

            # Remove markdown code blocks if present
            text = text.strip()
            if text.startswith("```"):
                # Use regex to find content between ```json and ``` or just ``` and ```
                match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
                if match:
                    text = match.group(1).strip()

            try:
                return json.loads(text)
            except json.JSONDecodeError:
                # Fallback: try to find anything that looks like a JSON object or array
                match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
                if match:
                    return json.loads(match.group(1))
                raise

        except json.JSONDecodeError as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(base_delay)
                continue
            raise ValueError(
                f"Failed to parse Gemini response as JSON after {max_retries} attempts: {e}"
            )

        except Exception as e:
            error_str = str(e)

            # Check for rate limit errors (429)
            if (
                "429" in error_str
                or "RESOURCE_EXHAUSTED" in error_str
                or "quota" in error_str.lower()
            ):
                retry_delay = _extract_retry_delay(error_str)

                if attempt < max_retries - 1:
                    print(
                        f"Rate limited. Waiting {retry_delay:.1f}s before retry {attempt + 2}/{max_retries}..."
                    )
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    raise ValueError(
                        f"Rate limit exceeded after {max_retries} attempts. "
                        f"Please wait a few minutes or check your Gemini API quota at https://ai.dev/rate-limit"
                    )

            # Other errors - retry with exponential backoff
            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)  # Exponential backoff
                print(f"Error: {e}. Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
                continue
            raise

    raise RuntimeError("Failed to generate JSON from Gemini.")


async def generate_text(prompt: str, max_retries: int = 3) -> str:
    """Generate text response from Gemini with rate limiting."""
    client = get_gemini_client()
    assert client is not None

    base_delay = 2.0

    for attempt in range(max_retries):
        try:
            await _rate_limit()

            response = await client.aio.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            if not response.text:
                raise ValueError("Gemini returned an empty response.")
            return response.text

        except Exception as e:
            error_str = str(e)

            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                retry_delay = _extract_retry_delay(error_str)

                if attempt < max_retries - 1:
                    print(f"Rate limited. Waiting {retry_delay:.1f}s before retry...")
                    await asyncio.sleep(retry_delay)
                    continue

            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                await asyncio.sleep(delay)
                continue
            raise

    raise RuntimeError("Failed to generate text from Gemini.")
