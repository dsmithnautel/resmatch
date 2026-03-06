"""Tests for the ingestion service."""

from unittest.mock import AsyncMock, patch

import pytest

from app.models.atomic_unit import AtomicUnit, AtomicUnitType, Evidence, SectionType, Tags
from app.services.ingestion import (
    SECTION_MAPPING,
    TYPE_MAPPING,
    _deduplicate_units,
    _normalize_text,
    _parse_raw_units,
    _text_similarity,
)

# ---------------------------------------------------------------------------
# Helpers to build AtomicUnit fixtures concisely
# ---------------------------------------------------------------------------


def _make_unit(
    *,
    text: str = "placeholder",
    section: SectionType = SectionType.EXPERIENCE,
    unit_type: AtomicUnitType = AtomicUnitType.BULLET,
    org: str | None = "Acme",
    role: str | None = "Engineer",
    skills: list[str] | None = None,
    email: str | None = None,
    phone: str | None = None,
    linkedin: str | None = None,
    github: str | None = None,
    unit_id: str = "test_000",
) -> AtomicUnit:
    return AtomicUnit(
        id=unit_id,
        type=unit_type,
        section=section,
        org=org,
        role=role,
        text=text,
        tags=Tags(
            skills=skills or [],
            email=email,
            phone=phone,
            linkedin=linkedin,
            github=github,
        ),
        evidence=Evidence(source="test.pdf", page=1),
        version="v_test",
    )


# ===========================================================================
# Mapping tables
# ===========================================================================


class TestTypeMappings:
    """Test the type and section mapping logic."""

    def test_type_mapping_standard_types(self):
        assert TYPE_MAPPING.get("bullet") == "bullet"
        assert TYPE_MAPPING.get("education") == "education"
        assert TYPE_MAPPING.get("project") == "project"
        assert TYPE_MAPPING.get("award") == "award"

    def test_type_mapping_section_to_type(self):
        assert TYPE_MAPPING.get("experience") == "bullet"
        assert TYPE_MAPPING.get("projects") == "project"
        assert TYPE_MAPPING.get("awards") == "award"
        assert TYPE_MAPPING.get("involvement") == "bullet"

    def test_section_mapping_variations(self):
        assert SECTION_MAPPING.get("work") == "experience"
        assert SECTION_MAPPING.get("employment") == "experience"
        assert SECTION_MAPPING.get("work experience") == "experience"

        assert SECTION_MAPPING.get("activities") == "involvement"
        assert SECTION_MAPPING.get("clubs") == "involvement"
        assert SECTION_MAPPING.get("extracurricular") == "involvement"

        assert SECTION_MAPPING.get("honors") == "awards"
        assert SECTION_MAPPING.get("achievements") == "awards"


# ===========================================================================
# _normalize_text
# ===========================================================================


class TestNormalizeText:
    def test_lowercases(self):
        assert _normalize_text("Hello World") == "hello world"

    def test_collapses_whitespace(self):
        assert _normalize_text("a   b\t\nc") == "a b c"

    def test_strips_edges(self):
        assert _normalize_text("  padded  ") == "padded"

    def test_empty_string(self):
        assert _normalize_text("") == ""


# ===========================================================================
# _text_similarity
# ===========================================================================


class TestTextSimilarity:
    def test_identical_strings(self):
        assert _text_similarity("hello world", "hello world") == 1.0

    def test_completely_different(self):
        assert _text_similarity("abcdef", "zyxwvu") < 0.3

    def test_case_insensitive(self):
        assert _text_similarity("Hello World", "hello world") == 1.0

    def test_whitespace_insensitive(self):
        assert _text_similarity("a  b  c", "a b c") == 1.0

    def test_near_duplicate_above_threshold(self):
        a = "Developed scalable backend services using Python and Go"
        b = "Developed scalable backend services using Python and Golang"
        assert _text_similarity(a, b) >= 0.85

    def test_different_bullets_below_threshold(self):
        a = "Developed scalable backend services using Python and Go"
        b = "Reduced API latency by 40% through caching optimizations"
        assert _text_similarity(a, b) < 0.85


# ===========================================================================
# _parse_raw_units
# ===========================================================================


class TestParseRawUnits:
    def test_basic_bullet(self):
        raw = [
            {
                "type": "bullet",
                "section": "experience",
                "org": "Google",
                "role": "SDE",
                "text": "Built a thing",
                "tags": {"skills": ["Python"], "domains": ["backend"], "seniority": "mid"},
            }
        ]
        units, warnings = _parse_raw_units(raw, "resume.pdf", "v1")
        assert len(units) == 1
        assert len(warnings) == 0
        u = units[0]
        assert u.org == "Google"
        assert u.role == "SDE"
        assert u.section == SectionType.EXPERIENCE
        assert u.type == AtomicUnitType.BULLET
        assert u.text == "Built a thing"
        assert u.tags.skills == ["Python"]
        assert u.evidence.source == "resume.pdf"
        assert u.version == "v1"

    def test_id_offset_avoids_collision(self):
        raw = [{"type": "bullet", "section": "experience", "org": "X", "text": "A"}]
        units_a, _ = _parse_raw_units(raw, "a.pdf", "v1", id_offset=0)
        units_b, _ = _parse_raw_units(raw, "b.pdf", "v1", id_offset=10)
        assert units_a[0].id != units_b[0].id
        assert "010" in units_b[0].id

    def test_unknown_section_mapped_to_other(self):
        raw = [{"type": "bullet", "section": "OBSCURE_SECTION", "org": "X", "text": "A"}]
        units, warnings = _parse_raw_units(raw, "f.pdf", "v1")
        assert len(units) == 1
        assert units[0].section == SectionType.OTHER
        assert any("Unknown section" in w for w in warnings)

    def test_unknown_type_defaults_to_bullet(self):
        raw = [{"type": "nonexistent_type", "section": "experience", "org": "X", "text": "A"}]
        units, _ = _parse_raw_units(raw, "f.pdf", "v1")
        assert units[0].type == AtomicUnitType.BULLET

    def test_missing_fields_use_defaults(self):
        raw = [{"text": "Just some text"}]
        units, _ = _parse_raw_units(raw, "f.pdf", "v1")
        assert len(units) == 1
        assert units[0].section == SectionType.EXPERIENCE
        assert units[0].type == AtomicUnitType.BULLET
        assert units[0].org is None

    def test_header_with_contact_tags(self):
        raw = [
            {
                "type": "header",
                "section": "header",
                "text": "John Doe",
                "tags": {
                    "skills": [],
                    "email": "john@example.com",
                    "phone": "555-1234",
                    "linkedin": "linkedin.com/in/john",
                    "github": "github.com/john",
                },
            }
        ]
        units, _ = _parse_raw_units(raw, "f.pdf", "v1")
        assert units[0].type == AtomicUnitType.HEADER
        assert units[0].tags.email == "john@example.com"
        assert units[0].tags.github == "github.com/john"

    def test_dates_parsed(self):
        raw = [
            {
                "type": "education",
                "section": "education",
                "org": "MIT",
                "text": "BS CS",
                "dates": {"start": "2020-08", "end": "2024-05"},
            }
        ]
        units, _ = _parse_raw_units(raw, "f.pdf", "v1")
        assert units[0].dates is not None
        assert units[0].dates.start == "2020-08"
        assert units[0].dates.end == "2024-05"

    def test_malformed_unit_produces_warning(self):
        raw = [
            {"type": "bullet", "section": "experience", "org": "Good", "text": "ok"},
            {"type": 123, "section": [], "text": object()},  # will fail validation
        ]
        units, warnings = _parse_raw_units(raw, "f.pdf", "v1")
        assert len(units) >= 1
        assert len(warnings) >= 1
        assert any("Failed to parse" in w for w in warnings)

    def test_empty_list(self):
        units, warnings = _parse_raw_units([], "f.pdf", "v1")
        assert units == []
        assert warnings == []


# ===========================================================================
# _deduplicate_units
# ===========================================================================


class TestDeduplicateUnits:
    # --- Headers ---

    def test_single_header_kept(self):
        h = _make_unit(
            text="John Doe",
            unit_type=AtomicUnitType.HEADER,
            section=SectionType.HEADER,
            email="j@x.com",
        )
        kept, removed = _deduplicate_units([h])
        assert len(kept) == 1
        assert removed == 0

    def test_multiple_headers_merged_to_best(self):
        h1 = _make_unit(
            text="John Doe",
            unit_type=AtomicUnitType.HEADER,
            section=SectionType.HEADER,
            email="j@x.com",
            phone="555-1234",
            unit_id="h1",
        )
        h2 = _make_unit(
            text="John Doe - Updated",
            unit_type=AtomicUnitType.HEADER,
            section=SectionType.HEADER,
            github="github.com/john",
            linkedin="linkedin.com/john",
            unit_id="h2",
        )
        kept, removed = _deduplicate_units([h1, h2])
        headers = [u for u in kept if u.type == AtomicUnitType.HEADER]
        assert len(headers) == 1
        assert removed == 1
        best = headers[0]
        assert best.tags.email == "j@x.com"
        assert best.tags.github == "github.com/john"
        assert best.tags.linkedin == "linkedin.com/john"

    # --- Skill groups ---

    def test_skill_groups_merged_by_category(self):
        sg1 = _make_unit(
            text="Python, Go",
            unit_type=AtomicUnitType.SKILL_GROUP,
            section=SectionType.SKILLS,
            org="Languages",
            skills=["Python", "Go"],
            unit_id="sg1",
        )
        sg2 = _make_unit(
            text="Python, Java, Rust",
            unit_type=AtomicUnitType.SKILL_GROUP,
            section=SectionType.SKILLS,
            org="Languages",
            skills=["Python", "Java", "Rust"],
            unit_id="sg2",
        )
        kept, removed = _deduplicate_units([sg1, sg2])
        skill_units = [u for u in kept if u.type == AtomicUnitType.SKILL_GROUP]
        assert len(skill_units) == 1
        assert removed == 1
        merged_skills = {s.lower() for s in skill_units[0].tags.skills}
        assert merged_skills == {"python", "go", "java", "rust"}

    def test_skill_groups_different_categories_kept_separate(self):
        sg1 = _make_unit(
            text="Python, Go",
            unit_type=AtomicUnitType.SKILL_GROUP,
            section=SectionType.SKILLS,
            org="Languages",
            skills=["Python", "Go"],
            unit_id="sg1",
        )
        sg2 = _make_unit(
            text="React, Vue",
            unit_type=AtomicUnitType.SKILL_GROUP,
            section=SectionType.SKILLS,
            org="Frameworks",
            skills=["React", "Vue"],
            unit_id="sg2",
        )
        kept, removed = _deduplicate_units([sg1, sg2])
        skill_units = [u for u in kept if u.type == AtomicUnitType.SKILL_GROUP]
        assert len(skill_units) == 2
        assert removed == 0

    def test_skill_group_keeps_longer_text(self):
        sg1 = _make_unit(
            text="Short",
            unit_type=AtomicUnitType.SKILL_GROUP,
            section=SectionType.SKILLS,
            org="Languages",
            skills=["Python"],
            unit_id="sg1",
        )
        sg2 = _make_unit(
            text="Python, Java, Go, Rust, TypeScript",
            unit_type=AtomicUnitType.SKILL_GROUP,
            section=SectionType.SKILLS,
            org="Languages",
            skills=["Python"],
            unit_id="sg2",
        )
        kept, _ = _deduplicate_units([sg1, sg2])
        skill_units = [u for u in kept if u.type == AtomicUnitType.SKILL_GROUP]
        assert skill_units[0].text == "Python, Java, Go, Rust, TypeScript"

    # --- Bullet / other dedup ---

    def test_exact_duplicate_bullets_removed(self):
        b1 = _make_unit(text="Reduced latency by 40%", unit_id="b1")
        b2 = _make_unit(text="Reduced latency by 40%", unit_id="b2")
        kept, removed = _deduplicate_units([b1, b2])
        bullets = [u for u in kept if u.type == AtomicUnitType.BULLET]
        assert len(bullets) == 1
        assert removed == 1

    def test_near_duplicate_bullets_removed(self):
        b1 = _make_unit(
            text="Developed scalable backend services using Python and Go",
            unit_id="b1",
        )
        b2 = _make_unit(
            text="Developed scalable backend services using Python and Golang",
            unit_id="b2",
        )
        kept, removed = _deduplicate_units([b1, b2])
        bullets = [u for u in kept if u.type == AtomicUnitType.BULLET]
        assert len(bullets) == 1
        assert removed == 1

    def test_keeps_longer_version_on_near_dup(self):
        short = _make_unit(
            text="Developed scalable backend services using Python and Go",
            unit_id="b1",
        )
        long = _make_unit(
            text="Developed scalable backend services using Python and Go at scale",
            unit_id="b2",
        )
        kept, _ = _deduplicate_units([short, long])
        bullets = [u for u in kept if u.type == AtomicUnitType.BULLET]
        assert len(bullets) == 1
        assert "at scale" in bullets[0].text

    def test_distinct_bullets_both_kept(self):
        b1 = _make_unit(text="Reduced latency by 40% through caching", unit_id="b1")
        b2 = _make_unit(
            text="Designed microservice architecture for payment processing",
            unit_id="b2",
        )
        kept, removed = _deduplicate_units([b1, b2])
        bullets = [u for u in kept if u.type == AtomicUnitType.BULLET]
        assert len(bullets) == 2
        assert removed == 0

    def test_different_org_role_not_compared(self):
        b1 = _make_unit(text="Wrote tests", org="Google", role="SDE", unit_id="b1")
        b2 = _make_unit(text="Wrote tests", org="Amazon", role="SDE", unit_id="b2")
        kept, removed = _deduplicate_units([b1, b2])
        bullets = [u for u in kept if u.type == AtomicUnitType.BULLET]
        assert len(bullets) == 2
        assert removed == 0

    # --- Mixed types ---

    def test_mixed_types_processed_correctly(self):
        header = _make_unit(
            text="Jane Doe",
            unit_type=AtomicUnitType.HEADER,
            section=SectionType.HEADER,
            email="jane@x.com",
            unit_id="h1",
        )
        skill = _make_unit(
            text="Python, Go",
            unit_type=AtomicUnitType.SKILL_GROUP,
            section=SectionType.SKILLS,
            org="Languages",
            skills=["Python", "Go"],
            unit_id="sg1",
        )
        bullet = _make_unit(text="Built a backend service", unit_id="b1")
        kept, removed = _deduplicate_units([header, skill, bullet])
        assert len(kept) == 3
        assert removed == 0

    def test_empty_list(self):
        kept, removed = _deduplicate_units([])
        assert kept == []
        assert removed == 0


# ===========================================================================
# ingest_pdf (async, mocked I/O)
# ===========================================================================


@pytest.fixture
def mock_ingestion_db():
    """Mock get_database where ingestion.py actually references it."""
    mock_db = AsyncMock()
    mock_db.atomic_units = AsyncMock()
    mock_db.master_versions = AsyncMock()

    with patch("app.services.ingestion.get_database", new_callable=AsyncMock, return_value=mock_db):
        yield mock_db


class TestIngestPdf:
    @pytest.mark.asyncio
    async def test_empty_pdf_returns_warning(self, mock_ingestion_db):
        with patch("app.services.ingestion._extract_text_from_pdf", return_value=""):
            from app.services.ingestion import ingest_pdf

            result = await ingest_pdf(b"fake-pdf-bytes", "empty.pdf")

        assert len(result.atomic_units) == 0
        assert any("Could not extract text" in w for w in result.warnings)

    @pytest.mark.asyncio
    async def test_gemini_failure_returns_warning(self, mock_ingestion_db):
        with (
            patch(
                "app.services.ingestion._extract_text_from_pdf",
                return_value="Some resume text",
            ),
            patch(
                "app.services.ingestion.generate_json",
                new_callable=AsyncMock,
                side_effect=Exception("API timeout"),
            ),
        ):
            from app.services.ingestion import ingest_pdf

            result = await ingest_pdf(b"fake-pdf-bytes", "bad.pdf")

        assert len(result.atomic_units) == 0
        assert any("Gemini extraction failed" in w for w in result.warnings)

    @pytest.mark.asyncio
    async def test_successful_single_pdf_ingestion(self, mock_ingestion_db):
        gemini_output = [
            {
                "type": "bullet",
                "section": "experience",
                "org": "Google",
                "role": "SDE",
                "text": "Built services",
                "tags": {"skills": ["Python"], "domains": ["backend"]},
            },
            {
                "type": "education",
                "section": "education",
                "org": "MIT",
                "role": "BS CS",
                "text": "Bachelor of Science",
                "tags": {"skills": [], "domains": []},
            },
        ]
        with (
            patch(
                "app.services.ingestion._extract_text_from_pdf",
                return_value="Resume text here",
            ),
            patch(
                "app.services.ingestion.generate_json",
                new_callable=AsyncMock,
                return_value=gemini_output,
            ),
        ):
            from app.services.ingestion import ingest_pdf

            result = await ingest_pdf(b"fake-pdf", "resume.pdf")

        assert len(result.atomic_units) == 2
        assert result.counts.get("experience") == 1
        assert result.counts.get("education") == 1
        assert result.merge_stats is None
        assert result.master_version_id.startswith("master_")
        mock_ingestion_db.master_versions.insert_one.assert_called_once()
        mock_ingestion_db.atomic_units.insert_many.assert_called_once()


# ===========================================================================
# ingest_multiple_pdfs (async, mocked I/O)
# ===========================================================================


class TestIngestMultiplePdfs:
    @pytest.mark.asyncio
    async def test_two_files_with_duplicates(self, mock_ingestion_db):
        shared_bullet = {
            "type": "bullet",
            "section": "experience",
            "org": "Google",
            "role": "SDE",
            "text": "Built scalable backend services using Python and Go",
            "tags": {"skills": ["Python", "Go"], "domains": ["backend"]},
        }
        unique_bullet = {
            "type": "bullet",
            "section": "experience",
            "org": "Google",
            "role": "SDE",
            "text": "Designed caching layer reducing latency by 40%",
            "tags": {"skills": ["Caching"], "domains": ["backend"]},
        }

        call_count = 0

        async def _mock_gemini(prompt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return [shared_bullet, unique_bullet]
            return [shared_bullet]

        with (
            patch(
                "app.services.ingestion._extract_text_from_pdf",
                return_value="Resume text",
            ),
            patch(
                "app.services.ingestion.generate_json",
                side_effect=_mock_gemini,
            ),
        ):
            from app.services.ingestion import ingest_multiple_pdfs

            result = await ingest_multiple_pdfs(
                [
                    (b"pdf1", "resume_v1.pdf"),
                    (b"pdf2", "resume_v2.pdf"),
                ]
            )

        assert result.merge_stats is not None
        assert result.merge_stats.files_processed == 2
        assert result.merge_stats.total_units_before_dedup == 3
        assert result.merge_stats.duplicates_removed == 1
        assert result.merge_stats.final_unit_count == 2
        assert len(result.atomic_units) == 2
        mock_ingestion_db.master_versions.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_one_file_fails_gracefully(self, mock_ingestion_db):
        good_bullet = {
            "type": "bullet",
            "section": "experience",
            "org": "Amazon",
            "text": "Led project",
            "tags": {"skills": ["Leadership"], "domains": []},
        }

        call_count = 0

        async def _mock_gemini(prompt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return [good_bullet]
            raise Exception("Gemini failed for file 2")

        with (
            patch(
                "app.services.ingestion._extract_text_from_pdf",
                return_value="Resume text",
            ),
            patch(
                "app.services.ingestion.generate_json",
                side_effect=_mock_gemini,
            ),
        ):
            from app.services.ingestion import ingest_multiple_pdfs

            result = await ingest_multiple_pdfs(
                [
                    (b"pdf1", "good.pdf"),
                    (b"pdf2", "bad.pdf"),
                ]
            )

        assert len(result.atomic_units) == 1
        assert result.merge_stats.files_processed == 2
        assert result.merge_stats.per_file_counts["good.pdf"] == 1
        assert result.merge_stats.per_file_counts["bad.pdf"] == 0
        assert any("Gemini extraction failed" in w for w in result.warnings)

    @pytest.mark.asyncio
    async def test_empty_pdf_skipped(self, mock_ingestion_db):
        good_bullet = {
            "type": "bullet",
            "section": "experience",
            "org": "X",
            "text": "Did work",
            "tags": {"skills": [], "domains": []},
        }

        call_count = 0

        def _extract(pdf_content):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return ""
            return "Resume text"

        async def _mock_gemini(prompt):
            return [good_bullet]

        with (
            patch(
                "app.services.ingestion._extract_text_from_pdf",
                side_effect=_extract,
            ),
            patch(
                "app.services.ingestion.generate_json",
                side_effect=_mock_gemini,
            ),
        ):
            from app.services.ingestion import ingest_multiple_pdfs

            result = await ingest_multiple_pdfs(
                [
                    (b"empty", "empty.pdf"),
                    (b"good", "good.pdf"),
                ]
            )

        assert result.merge_stats.per_file_counts["empty.pdf"] == 0
        assert result.merge_stats.per_file_counts["good.pdf"] == 1
        assert any("Could not extract text" in w for w in result.warnings)

    @pytest.mark.asyncio
    async def test_ids_reassigned_sequentially(self, mock_ingestion_db):
        bullets = [
            {
                "type": "bullet",
                "section": "experience",
                "org": "Google",
                "text": f"Bullet {i}",
                "tags": {"skills": [], "domains": []},
            }
            for i in range(3)
        ]

        async def _mock_gemini(prompt):
            return bullets

        with (
            patch(
                "app.services.ingestion._extract_text_from_pdf",
                return_value="Resume text",
            ),
            patch(
                "app.services.ingestion.generate_json",
                side_effect=_mock_gemini,
            ),
        ):
            from app.services.ingestion import ingest_multiple_pdfs

            result = await ingest_multiple_pdfs([(b"pdf1", "r.pdf")])

        ids = [u.id for u in result.atomic_units]
        assert ids == sorted(ids)
        for i, uid in enumerate(ids):
            assert uid.endswith(f"_{i:03d}")

    @pytest.mark.asyncio
    async def test_source_type_is_multi_pdf(self, mock_ingestion_db):
        async def _mock_gemini(prompt):
            return [
                {
                    "type": "bullet",
                    "section": "experience",
                    "org": "X",
                    "text": "A",
                    "tags": {"skills": [], "domains": []},
                }
            ]

        with (
            patch(
                "app.services.ingestion._extract_text_from_pdf",
                return_value="text",
            ),
            patch(
                "app.services.ingestion.generate_json",
                side_effect=_mock_gemini,
            ),
        ):
            from app.services.ingestion import ingest_multiple_pdfs

            result = await ingest_multiple_pdfs(
                [
                    (b"a", "a.pdf"),
                    (b"b", "b.pdf"),
                ]
            )

        stored = mock_ingestion_db.master_versions.insert_one.call_args[0][0]
        assert stored["source_type"] == "multi_pdf"
        assert stored["source_files"] == ["a.pdf", "b.pdf"]
        assert result.master_version_id.startswith("master_")
