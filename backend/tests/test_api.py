"""Integration tests for the FastAPI checkpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_services():
    """Consolidated service mocks for API tests."""
    with (
        patch("app.routers.job.parse_job_description", new_callable=AsyncMock) as m1,
        patch("app.routers.resume.tailor_units_against_jd", new_callable=AsyncMock) as m2,
        patch("app.routers.resume.render_resume", new_callable=AsyncMock) as m3,
        patch("app.routers.resume.get_database", new_callable=AsyncMock) as m4,
        patch("app.routers.job.get_database", new_callable=AsyncMock) as m5,
    ):
        yield {
            "parse_job_description": m1,
            "tailor_units_against_jd": m2,
            "render_resume": m3,
            "resume_db": m4,
            "job_db": m5,
        }


@pytest.mark.asyncio
async def test_health_check(async_client):
    """Test the health check endpoint."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_parse_job_url(async_client, mock_services):
    """Test the job parsing endpoint."""
    mock_jd_data = {
        "jd_id": "test_jd",
        "role_title": "Software Engineer",
        "company": "TestCorp",
        "must_haves": ["Python"],
        "nice_to_haves": [],
        "responsibilities": ["Coding"],
        "keywords": ["Python"],
        "source_url": "https://example.com",
    }

    from app.models import ParsedJD

    mock_jd = ParsedJD(**mock_jd_data)

    # Mock services
    mock_services["parse_job_description"].return_value = mock_jd

    # Mock DB via mock_services (patches app.routers.job.get_database)
    mock_db = MagicMock()
    mock_services["job_db"].return_value = mock_db
    mock_db.parsed_jds.insert_one = AsyncMock()

    response = await async_client.post("/job/parse", json={"url": "https://example.com"})

    assert response.status_code == 200
    assert response.json()["role_title"] == "Software Engineer"


@pytest.mark.asyncio
async def test_compile_resume(async_client, mock_services):
    """Test the resume compilation endpoint."""
    # Mock DB via mock_services (patches app.routers.resume.get_database)
    mock_db = MagicMock()
    mock_services["resume_db"].return_value = mock_db

    # Mock units cursor - need a proper async iterator for Python 3.11 compat
    class AsyncIterator:
        def __init__(self, items):
            self.items = items

        def __aiter__(self):
            return self

        async def __anext__(self):
            if not self.items:
                raise StopAsyncIteration
            return self.items.pop(0)

    mock_db.atomic_units.find.return_value = AsyncIterator(
        [{"unit_id": "u1", "text": "text", "section": "experience"}]
    )

    # Mock JD find
    mock_db.parsed_jds.find_one = AsyncMock(
        return_value={
            "jd_id": "jd1",
            "role_title": "SDE",
            "company": "Google",
            "must_haves": [],
        }
    )

    # Mock services
    from app.models import ScoredUnit

    mock_tailored = [
        ScoredUnit(
            unit_id="u1",
            text="tailored",
            section="experience",
            llm_score=9.0,
            matched_requirements=[],
            reasoning="",
        )
    ]
    mock_services["tailor_units_against_jd"].return_value = mock_tailored
    mock_services["render_resume"].return_value = "/tmp/resume.pdf"
    mock_db.compiles.insert_one = AsyncMock()

    response = await async_client.post(
        "/resume/compile", json={"master_version_id": "v1", "jd_id": "jd1"}
    )

    assert response.status_code == 200
    assert "compile_id" in response.json()
