"""Tests for Pydantic models."""

from app.models.atomic_unit import AtomicUnit, AtomicUnitType, Evidence, SectionType, Tags


def test_atomic_unit_creation():
    """Test creating an atomic unit with valid data."""
    unit = AtomicUnit(
        id="exp_test_001",
        type=AtomicUnitType.BULLET,
        section=SectionType.EXPERIENCE,
        org="Test Company",
        role="Software Engineer",
        text="Built amazing things",
        tags=Tags(skills=["Python"], domains=["backend"]),
        evidence=Evidence(source="test.pdf", page=1),
        version="v1",
    )

    assert unit.id == "exp_test_001"
    assert unit.type == AtomicUnitType.BULLET
    assert unit.section == SectionType.EXPERIENCE
    assert "Python" in unit.tags.skills


def test_atomic_unit_types():
    """Test all atomic unit types are valid."""
    valid_types = [
        "bullet",
        "skill_group",
        "education",
        "project",
        "header",
        "award",
        "certification",
        "publication",
        "language",
        "interest",
    ]

    for type_name in valid_types:
        assert AtomicUnitType(type_name) is not None


def test_section_types():
    """Test all section types are valid."""
    valid_sections = [
        "experience",
        "projects",
        "education",
        "skills",
        "header",
        "involvement",
        "leadership",
        "volunteer",
        "awards",
        "certifications",
        "publications",
        "languages",
        "interests",
        "other",
    ]

    for section_name in valid_sections:
        assert SectionType(section_name) is not None


def test_tags_optional_fields():
    """Test that tag fields are optional."""
    tags = Tags()
    assert tags.skills == []
    assert tags.domains == []
    assert tags.seniority is None

    tags_with_data = Tags(skills=["Python"], seniority="senior")
    assert tags_with_data.skills == ["Python"]
    assert tags_with_data.seniority == "senior"
