import asyncio
import os
import sys
from unittest.mock import MagicMock, patch

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.compile import ScoredUnit
from app.services.renderer import render_resume

# Mock data
MOCK_HEADER_UNITS = [
    {
        "type": "header",
        "text": "Jake Ryan",
        "tags": {"email": "jake@su.edu", "phone": "123-456-7890"},
    },
    {"type": "header", "text": "123-456-7890 | jake@su.edu", "tags": {}},
]

MOCK_SCORED_UNITS = [
    ScoredUnit(
        unit_id="exp1",
        text="Developed a REST API using FastAPI and PostgreSQL",
        section="Experience",
        org="Texas A&M University",
        role="Undergraduate Research Assistant",
        dates={"start": "June 2020", "end": "Present"},
        llm_score=9.0,
        selected=True,
    ),
    ScoredUnit(
        unit_id="exp2",
        text="Developed a full-stack web application using Flask, React, PostgreSQL and Docker",
        section="Experience",
        org="Texas A&M University",
        role="Undergraduate Research Assistant",
        dates={"start": "June 2020", "end": "Present"},
        llm_score=8.5,
        selected=True,
    ),
    ScoredUnit(
        unit_id="proj1",
        text="Developed a full-stack web application using with Flask serving a REST API with React as the frontend",
        section="Projects",
        org="Gitlytics",
        role="Full Stack Developer",  # Actually projects might simpler
        dates={"start": "June 2020", "end": "Present"},
        llm_score=9.0,
        selected=True,
    ),
    ScoredUnit(
        unit_id="skill1",
        text="Languages: Java, Python, C/C++, SQL (Postgres), JavaScript, HTML/CSS, R",
        section="Technical Skills",
        llm_score=10.0,
        selected=True,
    ),
]


class MockCursor:
    def __init__(self, data):
        self.data = data

    def __aiter__(self):
        self._iter = iter(self.data)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration


async def mock_get_database():
    mock_db = MagicMock()

    # Mock finding header units
    mock_cursor = MockCursor(MOCK_HEADER_UNITS)

    # Configure find to return our cursor
    mock_db.atomic_units.find.return_value = mock_cursor
    return mock_db


@patch("app.services.renderer.get_database", side_effect=mock_get_database)
async def run_test(mock_db_func):
    print("🚀 Starting LLM Renderer Test...")

    compile_id = "test_llm_compile_001"
    master_id = "test_master_v1"

    try:
        pdf_path = await render_resume(compile_id, MOCK_SCORED_UNITS, master_id)
        print(f"✅ Success! PDF generated at: {pdf_path}")

        # Verify file exists
        if os.path.exists(pdf_path):
            print(f"📄 File size: {os.path.getsize(pdf_path)} bytes")
        else:
            print("❌ File reported returned but not found on disk!")

    except Exception as e:
        print(f"❌ Test Failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️ GEMINI_API_KEY not found in env. Test might fail if not mocked.")

    asyncio.run(run_test())
