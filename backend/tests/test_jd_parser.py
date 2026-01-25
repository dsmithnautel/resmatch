"""Tests for the job description parser service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.jd_parser import parse_job_description, scrape_url


@pytest.mark.asyncio
async def test_scrape_url_trafilatura_success():
    """Test successful scraping using trafilatura."""
    mock_response = MagicMock()
    mock_response.text = "<html><body>Some job content</body></html>"
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        long_text = (
            "Extracted job content that is long enough to pass the 100 character threshold in the scrape_url function "
            * 2
        )
        with patch("trafilatura.extract", return_value=long_text) as mock_extract:
            result = await scrape_url("https://example.com/job")

    assert result == long_text
    mock_extract.assert_called_once()


@pytest.mark.asyncio
async def test_scrape_url_beautifulsoup_fallback():
    """Test fallback to BeautifulSoup when trafilatura fails."""
    mock_response = MagicMock()
    mock_response.text = (
        "<html><body><h1>Software Engineer</h1><p>Requirements...</p></body></html>"
    )
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        # trafilatura returns None or short text
        with patch("trafilatura.extract", return_value=""):
            result = await scrape_url("https://example.com/job")

    assert "Software Engineer" in result
    assert "Requirements" in result


@pytest.mark.asyncio
async def test_parse_job_description_with_url():
    """Test parsing a JD from a URL."""
    jd_text = "Software Engineer at Google. Must have Python."
    mock_gemini_response = {
        "role_title": "Software Engineer",
        "company": "Google",
        "must_haves": ["Python"],
        "nice_to_haves": ["Go"],
        "responsibilities": ["Coding"],
        "keywords": ["Python", "Go"],
    }

    with patch("app.services.jd_parser.scrape_url", new_callable=AsyncMock) as mock_scrape:
        mock_scrape.return_value = jd_text

        with patch("app.services.jd_parser.generate_json", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = mock_gemini_response
            result = await parse_job_description(url="https://google.com/jobs/1")

    assert result.role_title == "Software Engineer"
    assert result.company == "Google"
    assert "Python" in result.must_haves
    assert result.source_url == "https://google.com/jobs/1"


@pytest.mark.asyncio
async def test_parse_job_description_with_text():
    """Test parsing a JD from raw text."""
    jd_text = "Software Engineer at Google. Must have Python."
    mock_gemini_response = {
        "role_title": "Software Engineer",
        "company": "Google",
        "must_haves": ["Python"],
        "nice_to_haves": [],
        "responsibilities": [],
        "keywords": [],
    }

    with patch("app.services.jd_parser.generate_json", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_gemini_response
        result = await parse_job_description(text=jd_text)

    assert result.role_title == "Software Engineer"
    assert "Python" in result.must_haves
    assert result.raw_text.startswith(jd_text[:10])


@pytest.mark.asyncio
async def test_parse_job_description_gemini_failure():
    """Test that it returns a minimal JD when Gemini fails."""
    jd_text = "Some long job description text here..."

    with patch("app.services.jd_parser.generate_json", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = Exception("Gemini error")
        result = await parse_job_description(text=jd_text)

    assert result.role_title == "Unknown"
    assert result.company == "Unknown"
    assert result.must_haves == []
    assert result.raw_text.startswith("Some long job description")
