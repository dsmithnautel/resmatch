"""Tests for the resume selection optimizer."""

import pytest

from app.models import CompileConstraints, ParsedJD, ScoredUnit
from app.services.optimizer import optimize_selection


@pytest.fixture
def sample_parsed_jd():
    """Sample parsed JD for testing."""
    return ParsedJD(
        jd_id="jd_001",
        role_title="Software Engineer",
        company="TestCorp",
        must_haves=["Python", "FastAPI", "MongoDB"],
        nice_to_haves=["Docker"],
        responsibilities=["Build APIs"],
        keywords=["Python", "FastAPI"],
    )


@pytest.fixture
def sample_constraints():
    """Sample constraints for testing."""
    return CompileConstraints(
        max_experience_bullets=2,
        max_project_bullets=1,
        max_bullets_per_role=1,
        max_total_chars=1000,
    )


def test_optimize_selection_basic(sample_parsed_jd, sample_constraints):
    """Test basic selection logic."""
    scored_units = [
        ScoredUnit(
            unit_id="u1",
            text="Experienced Python developer",
            section="experience",
            org="Org1",
            role="Role1",
            llm_score=9.5,
            matched_requirements=["Python"],
        ),
        ScoredUnit(
            unit_id="u2",
            text="Built APIs with FastAPI",
            section="experience",
            org="Org1",
            role="Role1",
            llm_score=9.0,
            matched_requirements=["FastAPI"],
        ),
        ScoredUnit(
            unit_id="u3",
            text="MongoDB project",
            section="projects",
            org="Project1",
            role="Lead",
            llm_score=8.5,
            matched_requirements=["MongoDB"],
        ),
    ]

    selected, coverage = optimize_selection(scored_units, sample_parsed_jd, sample_constraints)

    # u2 should be skipped due to max_bullets_per_role limit for Org1_Role1
    assert len(selected) == 2
    assert selected[0].unit_id == "u1"
    assert selected[1].unit_id == "u3"
    assert coverage.must_haves_matched == 2  # Python and MongoDB


def test_optimize_selection_section_limits(sample_parsed_jd, sample_constraints):
    """Test that section limits are respected."""
    scored_units = [
        ScoredUnit(
            unit_id="u1",
            text="t1",
            section="experience",
            org="o1",
            role="r1",
            llm_score=9.0,
            matched_requirements=[],
        ),
        ScoredUnit(
            unit_id="u2",
            text="t2",
            section="experience",
            org="o2",
            role="r2",
            llm_score=8.0,
            matched_requirements=[],
        ),
        ScoredUnit(
            unit_id="u3",
            text="t3",
            section="experience",
            org="o3",
            role="r3",
            llm_score=7.0,
            matched_requirements=[],
        ),
    ]

    selected, _ = optimize_selection(scored_units, sample_parsed_jd, sample_constraints)

    # max_experience_bullets is 2
    assert len(selected) == 2


def test_optimize_selection_char_budget(sample_parsed_jd):
    """Test that character budget is respected."""
    constraints = CompileConstraints(
        max_experience_bullets=10,
        max_project_bullets=10,
        max_total_chars=1000,
    )
    scored_units = [
        ScoredUnit(
            unit_id="u1",
            text="A" * 900,
            section="experience",
            org="o1",
            role="r1",
            llm_score=9.0,
            matched_requirements=[],
        ),
        ScoredUnit(
            unit_id="u2",
            text="A" * 200,
            section="experience",
            org="o2",
            role="r2",
            llm_score=8.0,
            matched_requirements=[],
        ),
    ]

    selected, _ = optimize_selection(scored_units, sample_parsed_jd, constraints)

    # Only first one should fit (900 chars), second one (200 chars) would exceed 1000
    assert len(selected) == 1
    assert selected[0].unit_id == "u1"


def test_optimize_selection_score_threshold(sample_parsed_jd, sample_constraints):
    """Test that low scored units are skipped."""
    scored_units = [
        ScoredUnit(
            unit_id="u1",
            text="text",
            section="experience",
            org="o1",
            role="r1",
            llm_score=2.0,
            matched_requirements=[],
        ),
    ]

    selected, _ = optimize_selection(scored_units, sample_parsed_jd, sample_constraints)
    assert len(selected) == 0
