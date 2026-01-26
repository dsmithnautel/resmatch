"""Job Description parsing service."""

import uuid
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

from app.models import ParsedJD
from app.services.gemini import generate_json

JD_EXTRACTION_PROMPT = """
Parse this job description into structured requirements.

Return a JSON object with:
{
  "role_title": "exact job title",
  "company": "company name",
  "must_haves": ["required qualification 1", "required qualification 2", ...],
  "nice_to_haves": ["preferred qualification 1", ...],
  "responsibilities": ["key duty 1", "key duty 2", ...],
  "keywords": ["technical term 1", "tool 1", "framework 1", ...]
}

Classification rules:
- must_haves: Items with words like "required", "must have", "minimum", "X+ years required"
- nice_to_haves: Items with "preferred", "bonus", "nice to have", "ideally", "plus"
- responsibilities: Job duties, what you'll do, day-to-day tasks
- keywords: Technical skills, tools, frameworks, languages, methodologies (extract ALL mentioned)

Job Description:
"""


async def scrape_url(url: str) -> str:
    """Scrape text content from a job posting URL."""
    try:
        # Try trafilatura first (better for job boards)
        import trafilatura

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
            )
            response.raise_for_status()
            html = response.text

        # Extract main content
        text = trafilatura.extract(html)

        if text and len(text) > 100:
            return text

        # Fallback to BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Get text
        text = soup.get_text(separator="\n", strip=True)

        return text

    except Exception as e:
        raise ValueError(f"Failed to scrape URL: {str(e)}")


async def parse_job_description(url: str | None = None, text: str | None = None) -> ParsedJD:
    """
    Parse a job description from URL or text.

    Uses Gemini to extract structured requirements.
    """
    # Get the JD text
    if url:
        try:
            jd_text = await scrape_url(url)
        except Exception as e:
            if text:
                jd_text = text
            else:
                raise ValueError(f"Failed to scrape URL and no fallback text provided: {e}")
    elif text:
        jd_text = text
    else:
        raise ValueError("Either url or text must be provided")

    # Generate unique ID
    jd_id = f"jd_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"

    # Extract structured data using Gemini
    prompt = JD_EXTRACTION_PROMPT + jd_text[:8000]  # Limit to avoid token limits

    try:
        result = await generate_json(prompt)
    except Exception:
        # Return minimal parsed JD on failure
        return ParsedJD(
            jd_id=jd_id,
            role_title="Unknown",
            company="Unknown",
            must_haves=[],
            nice_to_haves=[],
            responsibilities=[],
            keywords=[],
            source_url=url,
            raw_text=jd_text[:5000],
        )

    return ParsedJD(
        jd_id=jd_id,
        role_title=result.get("role_title", "Unknown"),
        company=result.get("company", "Unknown"),
        must_haves=result.get("must_haves", []),
        nice_to_haves=result.get("nice_to_haves", []),
        responsibilities=result.get("responsibilities", []),
        keywords=result.get("keywords", []),
        source_url=url,
        raw_text=jd_text[:5000],
    )
