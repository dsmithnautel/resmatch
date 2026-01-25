"""Tests for the scoring and tailoring service."""

from unittest.mock import AsyncMock, patch

import pytest

from app.models import ParsedJD
from app.services.scoring import tailor_units_against_jd


@pytest.fixture
def sample_units():
    """Sample units for tailoring."""
    return [
        {"id": "b1", "text": "Built Python apps", "type": "bullet", "section": "experience", "org": "A", "role": "B"},
        {"id": "s1", "text": "Python, FastAPI", "type": "skill_group", "section": "skills"},
    ]


@pytest.fixture
def sample_parsed_jd():
    """Sample parsed JD."""
    return ParsedJD(
        jd_id="jd1",
        role_title="SDE",
        company="Google",
        must_haves=["Python"],
        nice_to_haves=[],
        responsibilities=[],
        keywords=["Python"],
    )


@pytest.mark.asyncio
async def test_tailor_units_against_jd_success(sample_units, sample_parsed_jd):
    """Test successful tailoring with Gemini."""
    mock_gemini_response = [
        {
            "id": "b1",
            "original_text": "Built Python apps",
            "tailored_text": "Engineered scalable Python applications",
            "score": 9.0,
            "changes_made": "Improved impact verbs",
        }
    ]

    with patch("app.services.scoring.generate_json", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_gemini_response
        result = await tailor_units_against_jd(sample_units, sample_parsed_jd)

    assert len(result) == 2  # 1 tailored + 1 passthrough (skill)
    
    # Check tailored unit
    tailored = next(u for u in result if u.unit_id == "b1")
    assert tailored.text == "Engineered scalable Python applications"
    assert tailored.llm_score == 9.0
    
    # Check passthrough unit
    skill = next(u for u in result if u.unit_id == "s1")
    assert skill.text == "Python, FastAPI"
    assert skill.llm_score == 10.0


@pytest.mark.asyncio
async def test_tailor_units_against_jd_failure(sample_units, sample_parsed_jd):
    """Test handles Gemini failure by falling back to original text."""
    with patch("app.services.scoring.generate_json", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = Exception("Gemini down")
        result = await tailor_units_against_jd(sample_units, sample_parsed_jd)

    assert len(result) == 2
    b1 = next(u for u in result if u.unit_id == "b1")
    assert b1.text == "Built Python apps"
    assert b1.llm_score == 5.0
    assert "failed" in b1.reasoning.lower()
