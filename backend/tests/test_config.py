"""Tests for the configuration and settings."""

import os
from unittest.mock import patch

from app.config import Settings, parse_cors_origins, validate_settings


def test_parse_cors_origins_json():
    """Test parsing JSON array from CORS_ORIGINS."""
    with patch.dict(os.environ, {"CORS_ORIGINS": '["http://a.com", "http://b.com"]'}):
        origins = parse_cors_origins()
    assert origins == ["http://a.com", "http://b.com"]


def test_parse_cors_origins_csv():
    """Test parsing comma-separated origins."""
    with patch.dict(os.environ, {"CORS_ORIGINS": "http://a.com, http://b.com"}):
        origins = parse_cors_origins()
    assert origins == ["http://a.com", "http://b.com"]


def test_parse_cors_origins_single():
    """Test parsing a single origin."""
    with patch.dict(os.environ, {"CORS_ORIGINS": "http://a.com"}):
        origins = parse_cors_origins()
    assert origins == ["http://a.com"]


def test_validate_settings_missing_gemini_key():
    """Test validation fails when Gemini key is missing in production."""
    settings = Settings(gemini_api_key="", environment="production")
    
    with patch("sys.exit") as mock_exit:
        validate_settings(settings)
        mock_exit.assert_called_once_with(1)


def test_validate_settings_warning_on_localhost_prod():
    """Test warning when using localhost DB in production."""
    settings = Settings(
        gemini_api_key="key", 
        environment="production", 
        mongodb_uri="mongodb://localhost:27017"
    )
    
    with patch("builtins.print") as mock_print:
        warnings = validate_settings(settings)
        assert any("localhost" in str(args[0]) for args, kwargs in mock_print.call_args_list)
        assert len(warnings) > 0
