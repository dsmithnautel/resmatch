"""Pytest configuration and fixtures."""

import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["GEMINI_API_KEY"] = "test-key-for-testing"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017"
os.environ["MONGODB_DATABASE"] = "resume_compile_test"


@pytest.fixture(autouse=True)
def mock_external_deps():
    """Globally mock external dependencies to prevent CI failures."""
    with (
        patch("app.db.mongodb.get_database", new_callable=AsyncMock) as mock_db,
        patch("google.genai.Client", autospec=True) as mock_genai,
        patch("subprocess.run") as mock_run,
        patch("shutil.which", return_value="/usr/bin/pdflatex"),
        patch("app.services.gemini._rate_limit", new_callable=AsyncMock),
    ):
        # Setup default mock behavior for MongoDB
        db_instance = AsyncMock()
        mock_db.return_value = db_instance

        # Setup default mock for subprocess
        mock_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")

        yield {"db": db_instance, "genai": mock_genai, "run": mock_run}


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client():
    """Create an async test client for the FastAPI app."""
    from httpx import ASGITransport, AsyncClient

    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_gemini():
    """Mock Gemini API responses."""
    with patch("app.services.gemini.generate_json") as mock:
        mock.return_value = []
        yield mock


@pytest.fixture
def mock_mongodb():
    """Mock MongoDB operations."""
    mock_db = AsyncMock()
    mock_db.atomic_units = AsyncMock()
    mock_db.master_versions = AsyncMock()
    mock_db.job_descriptions = AsyncMock()
    mock_db.compiles = AsyncMock()

    with patch("app.db.mongodb.get_database", return_value=mock_db):
        yield mock_db


@pytest.fixture
def sample_atomic_units():
    """Sample atomic units for testing."""
    return [
        {
            "id": "exp_google_001",
            "type": "bullet",
            "section": "experience",
            "org": "Google",
            "role": "Software Engineer",
            "text": "Developed scalable backend services using Python and Go",
            "tags": {
                "skills": ["Python", "Go", "Backend"],
                "domains": ["backend"],
                "seniority": "mid",
            },
        },
        {
            "id": "exp_google_002",
            "type": "bullet",
            "section": "experience",
            "org": "Google",
            "role": "Software Engineer",
            "text": "Reduced API latency by 40% through caching optimizations",
            "tags": {
                "skills": ["Performance", "Caching"],
                "domains": ["backend"],
                "seniority": "mid",
            },
        },
    ]


@pytest.fixture
def sample_jd():
    """Sample job description for testing."""
    return {
        "jd_id": "jd_test_001",
        "role_title": "Senior Software Engineer",
        "company": "TechCorp",
        "must_haves": ["5+ years Python experience", "Experience with distributed systems"],
        "nice_to_haves": ["Go experience", "Kubernetes knowledge"],
        "responsibilities": ["Design and implement backend services", "Mentor junior engineers"],
        "keywords": ["Python", "Go", "Distributed Systems", "Kubernetes"],
    }
