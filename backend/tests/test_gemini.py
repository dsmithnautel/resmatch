"""Tests for the Gemini API client wrapper."""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.services.gemini import _extract_retry_delay, generate_json, generate_text


@pytest.mark.parametrize(
    "error_message,expected_delay",
    [
        ("retry in 15.5s", 15.5),
        ("retryDelay: '42s'", 42.0),
        ("quota exceeded, try again in 60s", 60.0),
        ("no delay mentioned here", 60.0),
    ],
)
def test_extract_retry_delay(error_message, expected_delay):
    """Test extracting retry delay from various error message formats."""
    assert _extract_retry_delay(error_message) == expected_delay


@pytest.mark.asyncio
async def test_generate_json_success():
    """Test successful JSON generation from Gemini."""
    mock_response = MagicMock()
    mock_response.text = '{"key": "value"}'

    with patch("app.services.gemini.get_gemini_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client

        # Mock sleep to avoid waiting during tests
        with patch("asyncio.sleep", return_value=None):
            result = await generate_json("test prompt")

    assert result == {"key": "value"}
    mock_client.models.generate_content.assert_called_once()


@pytest.mark.asyncio
async def test_generate_json_with_markdown():
    """Test JSON generation when Gemini includes markdown code blocks."""
    mock_response = MagicMock()
    mock_response.text = '```json\n{"key": "value"}\n```'

    with patch("app.services.gemini.get_gemini_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client

        with patch("asyncio.sleep", return_value=None):
            result = await generate_json("test prompt")

    assert result == {"key": "value"}


@pytest.mark.asyncio
async def test_generate_json_retry_on_decode_error():
    """Test that it retries when Gemini returns invalid JSON."""
    mock_response_invalid = MagicMock()
    mock_response_invalid.text = "invalid json"

    mock_response_valid = MagicMock()
    mock_response_valid.text = '{"key": "value"}'

    with patch("app.services.gemini.get_gemini_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = [
            mock_response_invalid,
            mock_response_valid,
        ]
        mock_get_client.return_value = mock_client

        with patch("asyncio.sleep", return_value=None):
            result = await generate_json("test prompt", max_retries=2)

    assert result == {"key": "value"}
    assert mock_client.models.generate_content.call_count == 2


@pytest.mark.asyncio
async def test_generate_json_rate_limit_retry():
    """Test that it retries on 429 rate limit errors."""
    error_429 = Exception("Resource has been exhausted (e.g. check quota). 429")

    mock_response_valid = MagicMock()
    mock_response_valid.text = '{"success": true}'

    with patch("app.services.gemini.get_gemini_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = [error_429, mock_response_valid]
        mock_get_client.return_value = mock_client

        with patch("asyncio.sleep", return_value=None) as mock_sleep:
            result = await generate_json("test prompt", max_retries=2)

    assert result == {"success": True}
    assert mock_client.models.generate_content.call_count == 2
    mock_sleep.assert_called()


@pytest.mark.asyncio
async def test_generate_text_success():
    """Test successful text generation."""
    mock_response = MagicMock()
    mock_response.text = "Hello world"

    with patch("app.services.gemini.get_gemini_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client

        with patch("asyncio.sleep", return_value=None):
            result = await generate_text("test prompt")

    assert result == "Hello world"
