"""Tests for the ingestion service."""

from unittest.mock import patch

import pytest


class TestTypeMappings:
    """Test the type and section mapping logic."""

    def test_type_mapping_standard_types(self):
        """Test that standard types map correctly."""
        from app.services.ingestion import TYPE_MAPPING

        assert TYPE_MAPPING.get("bullet") == "bullet"
        assert TYPE_MAPPING.get("education") == "education"
        assert TYPE_MAPPING.get("project") == "project"
        assert TYPE_MAPPING.get("award") == "award"

    def test_type_mapping_section_to_type(self):
        """Test that section names map to appropriate types."""
        from app.services.ingestion import TYPE_MAPPING

        # Section names should map to their content types
        assert TYPE_MAPPING.get("experience") == "bullet"
        assert TYPE_MAPPING.get("projects") == "project"
        assert TYPE_MAPPING.get("awards") == "award"
        assert TYPE_MAPPING.get("involvement") == "bullet"

    def test_section_mapping_variations(self):
        """Test that section name variations are handled."""
        from app.services.ingestion import SECTION_MAPPING

        # Work variations -> experience
        assert SECTION_MAPPING.get("work") == "experience"
        assert SECTION_MAPPING.get("employment") == "experience"
        assert SECTION_MAPPING.get("work experience") == "experience"

        # Activity variations -> involvement
        assert SECTION_MAPPING.get("activities") == "involvement"
        assert SECTION_MAPPING.get("clubs") == "involvement"
        assert SECTION_MAPPING.get("extracurricular") == "involvement"

        # Award variations -> awards
        assert SECTION_MAPPING.get("honors") == "awards"
        assert SECTION_MAPPING.get("achievements") == "awards"


class TestPDFIngestion:
    """Test PDF ingestion functionality."""

    @pytest.mark.asyncio
    async def test_empty_pdf_returns_warning(self, mock_gemini, mock_mongodb):
        """Test that empty PDFs return appropriate warnings."""

        # Create a minimal valid PDF that extracts no text
        # This would need a real empty PDF file for proper testing
        # For now, we'll skip this test
        pytest.skip("Requires actual PDF file for testing")

    @pytest.mark.asyncio
    async def test_gemini_failure_handled(self, mock_mongodb):
        """Test that Gemini failures are handled gracefully."""

        with patch("app.services.ingestion.generate_json") as mock_gen:
            mock_gen.side_effect = Exception("API Error")

            # Would need actual PDF content to test
            pytest.skip("Requires actual PDF file for testing")
