import pytest

from app.models import ScoredUnit
from app.services.rendercv_mapper import map_to_rendercv_model


@pytest.fixture
def sample_header():
    """Sample header info."""
    return {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "555-1234",
        "linkedin": "https://linkedin.com/in/johndoe",
        "github": "https://github.com/johndoe",
    }


def test_map_to_rendercv_model_basic(sample_header):
    """Test mapping units to RenderCV structure."""
    # Atomic units to be tailored
    units = [
        ScoredUnit(
            unit_id="u1",
            text="Developed Python apps",
            section="experience",
            org="Google",
            role="SWE",
            llm_score=9.0,
            dates={"start": "2020-01", "end": "2021-01"},
        ),
        ScoredUnit(
            unit_id="u2",
            text="Bachelor of Science",
            section="education",
            org="Stanford",
            role="BS CS",
            llm_score=10.0,
            dates={"start": "2016-09", "end": "2020-06"},
        ),
        ScoredUnit(
            unit_id="s1",
            text="Python, FastAPI, Docker",
            section="skills",
            llm_score=10.0,
            tags={"skills": ["Python", "FastAPI", "Docker"]},
        ),
    ]

    model = map_to_rendercv_model(units, sample_header)

    assert model["cv"]["name"] == "John Doe"
    assert "experience" in model["cv"]["sections"]
    assert "education" in model["cv"]["sections"]
    assert "technical_skills" in model["cv"]["sections"]

    # Check experience mapping
    exp = model["cv"]["sections"]["experience"][0]
    assert exp["company"] == "Google"
    assert exp["position"] == "SWE"
    assert "Developed Python apps" in exp["highlights"]

    # Check skills categorizing
    skills = model["cv"]["sections"]["technical_skills"]
    assert any(s["label"] == "Languages" and "Python" in s["details"] for s in skills)
    assert any(s["label"] == "Frameworks" and "FastAPI" in s["details"] for s in skills)
    assert any(s["label"] == "Tools" and "Docker" in s["details"] for s in skills)
