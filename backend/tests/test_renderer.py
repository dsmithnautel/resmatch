"""Tests for the resume renderer service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models import ScoredUnit
from app.services.renderer import extract_header_info, render_resume


def test_extract_header_info_basic():
    """Test extracting contact info from header units."""
    header_units = [
        {"text": "John Doe\nSoftware Engineer"},
        {"text": "john.doe@example.com | (555) 123-4567"},
        {"text": "linkedin.com/in/johndoe | github.com/johndoe"},
    ]
    info = extract_header_info(header_units)

    assert info["name"] == "John Doe"
    assert info["email"] == "john.doe@example.com"
    assert info["phone"] == "(555) 123-4567"
    assert "linkedin.com/in/johndoe" in info["linkedin"]
    assert "github.com/johndoe" in info["github"]


def test_extract_header_info_empty():
    """Test handling empty header units."""
    assert extract_header_info([]) == {}


@pytest.mark.asyncio
async def test_render_resume_success():
    """Test successful resume rendering orchestration."""
    compile_id = "test_compile"
    master_version_id = "test_master"
    selected_units = [
        ScoredUnit(
            unit_id="u1", text="text", section="experience", org="o1", role="r1", llm_score=9.0
        )
    ]

    mock_db = MagicMock()
    mock_db.atomic_units = MagicMock()
    # Mock the return value of find() to be an object that has __aiter__
    mock_cursor = AsyncMock()
    mock_cursor.__aiter__.return_value = [{"text": "John Doe", "type": "header"}]
    mock_db.atomic_units.find.return_value = mock_cursor

    mock_cv_data = {"cv": {"name": "John Doe"}}

    with (
        patch("app.services.renderer.get_database", return_value=mock_db),
        patch("app.services.renderer.map_to_rendercv_model", return_value=mock_cv_data),
        patch("os.makedirs"),
        patch("builtins.open", MagicMock()),
        patch("yaml.dump"),
        patch("subprocess.run") as mock_run,
        patch("os.path.exists", return_value=True),
        patch("os.walk", return_value=[("/tmp/out", [], ["John_Doe_CV.pdf"])]),
        patch("shutil.move") as mock_move,
        patch("shutil.rmtree"),
    ):
        mock_run.return_value = MagicMock(stdout="Success", stderr="")

        # Simulate PDF finding logic
        # We need to control os.path.exists and os.walk to find the PDF
        with patch("app.services.renderer.os.path.exists", side_effect=[True, True, True, True]):
            result = await render_resume(compile_id, selected_units, master_version_id)

    assert "resume.pdf" in result
    mock_run.assert_called_once()
    mock_move.assert_called_once()


@pytest.mark.asyncio
async def test_render_resume_failure():
    """Test handling RenderCV failure."""
    compile_id = "test_compile"
    selected_units = []

    mock_db = MagicMock()
    mock_db.atomic_units = MagicMock()
    mock_cursor = AsyncMock()
    mock_cursor.__aiter__.return_value = []
    mock_db.atomic_units.find.return_value = mock_cursor

    with (
        patch("app.services.renderer.get_database", return_value=mock_db),
        patch("os.makedirs"),
        patch("builtins.open", MagicMock()),
        patch("subprocess.run") as mock_run,
    ):
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="LaTeX error")

        with pytest.raises(RuntimeError, match="RenderCV compilation failed"):
            await render_resume(compile_id, selected_units, "v1")
