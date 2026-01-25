"""Integration tests for the FastAPI checkpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_services():
    """Consolidated service mocks for API tests."""
    with patch("app.routers.job.parse_job_description") as m1, \
         patch("app.routers.resume.tailor_units_against_jd") as m2, \
         patch("app.routers.resume.render_resume") as m3, \
         patch("app.routers.resume.get_database") as m4, \
         patch("app.routers.job.get_database") as m5:
        yield {
            "parse_job_description": m1,
            "tailor_units_against_jd": m2,
            "render_resume": m3,
            "resume_db": m4,
            "job_db": m5
        }


@pytest.mark.asyncio
async def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_parse_job_url(client, mock_services):
    """Test the job parsing endpoint."""
    mock_jd = MagicMock()
    mock_jd.model_dump.return_value = {
        "jd_id": "test_jd",
        "role_title": "Software Engineer",
        "company": "TestCorp",
        "must_haves": ["Python"],
        "nice_to_haves": [],
        "responsibilities": [],
        "keywords": ["Python"],
        "source_url": "https://example.com",
    }
    mock_jd.role_title = "Software Engineer"
    
    mock_services["parse_job_description"].side_effect = AsyncMock(return_value=mock_jd)
    
    # Mock DB
    mock_db = AsyncMock()
    mock_services["job_db"].return_value = mock_db
    mock_db.parsed_jds.insert_one = AsyncMock()

    response = client.post("/job/parse", json={"url": "https://example.com"})

    assert response.status_code == 200
    assert response.json()["role_title"] == "Software Engineer"


@pytest.mark.asyncio
async def test_compile_resume(client, mock_services):
    """Test the resume compilation endpoint."""
    # Mock DB
    mock_db = AsyncMock()
    mock_services["resume_db"].return_value = mock_db
    
    # Mock units cursor
    mock_cursor = AsyncMock()
    mock_cursor.__aiter__.return_value = [
        {"unit_id": "u1", "text": "text", "section": "experience"}
    ]
    mock_db.atomic_units.find.return_value = mock_cursor
    
    # Mock JD find
    mock_db.parsed_jds.find_one.return_value = {
        "jd_id": "jd1", "role_title": "SDE", "company": "Google", "must_haves": []
    }
    
    # Mock services
    mock_tailored = [
        MagicMock(unit_id="u1", text="tailored", section="experience", llm_score=9.0, matched_requirements=[], reasoning="")
    ]
    mock_services["tailor_units_against_jd"].side_effect = AsyncMock(return_value=mock_tailored)
    mock_services["render_resume"].side_effect = AsyncMock(return_value="/tmp/resume.pdf")
    mock_db.compiles.insert_one = AsyncMock()
    
    response = client.post("/resume/compile", json={
        "master_version_id": "v1",
        "jd_id": "jd1"
    })
            
    assert response.status_code == 200
    assert "compile_id" in response.json()
