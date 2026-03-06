"""PDF ingestion service - extracts atomic units from master resume."""

import hashlib
import re
from datetime import datetime
from difflib import SequenceMatcher

import fitz  # PyMuPDF

from app.db.mongodb import get_database
from app.models import AtomicUnit, MasterResumeResponse, MasterVersion
from app.models.atomic_unit import AtomicUnitType, DateRange, Evidence, SectionType, Tags
from app.models.master_resume import MergeStats
from app.services.gemini import generate_json

EXTRACTION_PROMPT = """
You are a resume parser. Extract ALL content from this resume into atomic units.
Each unit is ONE bullet point, skill group, education entry, project, award, etc.

Return a JSON array. For EACH unit, include:
{
  "type": "bullet" | "skill_group" | "education" | "project" | "header" | "award" | "certification" | "publication" | "language" | "interest",
  "section": "experience" | "projects" | "education" | "skills" | "header" | "involvement" | "leadership" | "volunteer" | "awards" | "certifications" | "publications" | "languages" | "interests" | "other",
  "org": "company/school/organization name (or null)",
  "role": "job title, degree, or position (or null)",
  "dates": {"start": "YYYY-MM or null", "end": "YYYY-MM or present or null"},
  "text": "EXACT text from resume - DO NOT modify, summarize, or expand",
  "tags": {
    "skills": ["skill1", "skill2", ...],
    "domains": ["backend", "frontend", "ml", "data", "devops", "mobile", etc.],
    "seniority": "intern" | "entry" | "mid" | "senior" | "staff" | null
  }
}

SECTION MAPPING:
- Experience, Work History, Employment → section: "experience", type: "bullet"
- Projects, Personal Projects → section: "projects", type: "project"
- Education, Academic → section: "education", type: "education"
- Skills, Technical Skills → section: "skills", type: "skill_group"
- Involvement, Activities, Clubs, Organizations → section: "involvement", type: "bullet"
- Leadership, Leadership Experience → section: "leadership", type: "bullet"
- Volunteer, Community Service → section: "volunteer", type: "bullet"
- Awards, Honors, Achievements → section: "awards", type: "award"
- Certifications, Licenses → section: "certifications", type: "certification"
- Publications, Papers, Research → section: "publications", type: "publication"
- Languages → section: "languages", type: "language"
- Interests, Hobbies → section: "interests", type: "interest"
- Any other unrecognized section → section: "other", type: "bullet"

CRITICAL RULES:
1. Use ONLY text that appears VERBATIM in the resume
2. Do NOT infer, expand, or add any information
3. Do NOT merge multiple bullets into one
4. If dates are unclear, use null
5. Extract EVERY bullet point, even short ones
6. For skills section, create one skill_group per category. Put the category name (e.g. "Languages", "Frameworks") in the "org" field.
7. For "header" section, create ONE unit. Put name in "text". Store exact "phone", "email", "linkedin", "github" values in the "tags" dictionary.
8. Recognize ALL sections, not just standard ones

Resume text:
"""

# Map invalid types to valid AtomicUnitTypes
# Gemini sometimes confuses section names with type names
TYPE_MAPPING = {
    # Standard types (valid as-is)
    "bullet": "bullet",
    "skill_group": "skill_group",
    "education": "education",
    "project": "project",
    "header": "header",
    "award": "award",
    "certification": "certification",
    "publication": "publication",
    "language": "language",
    "interest": "interest",
    # Section names that should map to types
    "experience": "bullet",
    "projects": "project",
    "skills": "skill_group",
    "involvement": "bullet",
    "leadership": "bullet",
    "volunteer": "bullet",
    "awards": "award",
    "certifications": "certification",
    "publications": "publication",
    "languages": "language",
    "interests": "interest",
    # Common variations
    "activities": "bullet",
    "honors": "award",
    "achievements": "award",
    "papers": "publication",
    "research": "publication",
    "hobbies": "interest",
}

# Map section name variations to standard SectionType values
SECTION_MAPPING = {
    "experience": "experience",
    "work": "experience",
    "work experience": "experience",
    "employment": "experience",
    "projects": "projects",
    "personal projects": "projects",
    "education": "education",
    "academic": "education",
    "skills": "skills",
    "technical skills": "skills",
    "header": "header",
    "involvement": "involvement",
    "activities": "involvement",
    "clubs": "involvement",
    "organizations": "involvement",
    "extracurricular": "involvement",
    "leadership": "leadership",
    "leadership experience": "leadership",
    "volunteer": "volunteer",
    "volunteering": "volunteer",
    "community service": "volunteer",
    "awards": "awards",
    "honors": "awards",
    "achievements": "awards",
    "certifications": "certifications",
    "licenses": "certifications",
    "certificates": "certifications",
    "publications": "publications",
    "papers": "publications",
    "research": "publications",
    "languages": "languages",
    "interests": "interests",
    "hobbies": "interests",
    "other": "other",
}


def _extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract raw text from a PDF using PyMuPDF."""
    doc = fitz.open(stream=pdf_content, filetype="pdf")
    full_text = ""
    for page_num, page in enumerate(doc):
        text = page.get_text()
        text = text.replace("\0", "").strip()
        if text:
            full_text += f"\n--- Page {page_num + 1} ---\n"
            full_text += text
    doc.close()
    return full_text


def _parse_raw_units(
    raw_units: list[dict],
    filename: str,
    version_id: str,
    id_offset: int = 0,
) -> tuple[list[AtomicUnit], list[str]]:
    """
    Parse raw Gemini JSON output into validated AtomicUnit objects.
    Returns (units, warnings). id_offset avoids ID collisions across files.
    """
    atomic_units: list[AtomicUnit] = []
    warnings: list[str] = []

    for i, raw in enumerate(raw_units):
        global_idx = i + id_offset
        try:
            raw_section = raw.get("section", "experience").lower()
            normalized_section = SECTION_MAPPING.get(raw_section, raw_section)

            valid_sections = [s.value for s in SectionType]
            if normalized_section not in valid_sections:
                normalized_section = "other"
                warnings.append(
                    f"Unit {global_idx}: Unknown section '{raw_section}' mapped to 'other'"
                )

            org = raw.get("org", "unknown")
            org_slug = "".join(c for c in (org or "unknown")[:10].lower() if c.isalnum())
            unit_id = f"{normalized_section[:3]}_{org_slug}_{global_idx:03d}"

            dates = None
            if raw.get("dates"):
                dates = DateRange(start=raw["dates"].get("start"), end=raw["dates"].get("end"))

            tags = Tags(
                skills=raw.get("tags", {}).get("skills", []),
                domains=raw.get("tags", {}).get("domains", []),
                seniority=raw.get("tags", {}).get("seniority"),
                email=raw.get("tags", {}).get("email"),
                phone=raw.get("tags", {}).get("phone"),
                linkedin=raw.get("tags", {}).get("linkedin"),
                github=raw.get("tags", {}).get("github"),
            )

            raw_type = raw.get("type", "bullet").lower()
            normalized_type = TYPE_MAPPING.get(raw_type, "bullet")

            unit = AtomicUnit(
                id=unit_id,
                type=AtomicUnitType(normalized_type),
                section=SectionType(normalized_section),
                org=raw.get("org"),
                role=raw.get("role"),
                dates=dates,
                text=raw.get("text", ""),
                tags=tags,
                evidence=Evidence(source=filename, page=1),
                version=version_id,
            )

            atomic_units.append(unit)
        except Exception as e:
            warnings.append(f"Failed to parse unit {global_idx}: {str(e)}")

    return atomic_units, warnings


def _normalize_text(text: str) -> str:
    """Normalize text for comparison: lowercase, collapse whitespace, strip punctuation edges."""
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _text_similarity(a: str, b: str) -> float:
    """Return 0-1 similarity score between two strings."""
    return SequenceMatcher(None, _normalize_text(a), _normalize_text(b)).ratio()


_DEDUP_SIMILARITY_THRESHOLD = 0.85


def _deduplicate_units(all_units: list[AtomicUnit]) -> tuple[list[AtomicUnit], int]:
    """
    Remove duplicate/near-duplicate atomic units across multiple files.

    Strategy by unit type:
      - header:      keep the one with the most contact fields populated
      - skill_group: merge skills lists for groups with the same category (org)
      - all others:  text similarity; keep the longer/more detailed version

    Returns (deduplicated_units, num_removed).
    """
    headers: list[AtomicUnit] = []
    skill_groups: list[AtomicUnit] = []
    other_units: list[AtomicUnit] = []

    for u in all_units:
        if u.type == AtomicUnitType.HEADER:
            headers.append(u)
        elif u.type == AtomicUnitType.SKILL_GROUP:
            skill_groups.append(u)
        else:
            other_units.append(u)

    kept: list[AtomicUnit] = []

    # --- Headers: keep the most complete one ---
    if headers:

        def _header_completeness(h: AtomicUnit) -> int:
            score = 0
            if h.tags.email:
                score += 1
            if h.tags.phone:
                score += 1
            if h.tags.linkedin:
                score += 1
            if h.tags.github:
                score += 1
            score += len(h.text)
            return score

        best = max(headers, key=_header_completeness)
        # Merge any contact info the best header is missing
        for h in headers:
            if h is best:
                continue
            if not best.tags.email and h.tags.email:
                best.tags.email = h.tags.email
            if not best.tags.phone and h.tags.phone:
                best.tags.phone = h.tags.phone
            if not best.tags.linkedin and h.tags.linkedin:
                best.tags.linkedin = h.tags.linkedin
            if not best.tags.github and h.tags.github:
                best.tags.github = h.tags.github
        kept.append(best)

    # --- Skill groups: merge by category (org field) ---
    skill_map: dict[str, AtomicUnit] = {}
    for sg in skill_groups:
        key = _normalize_text(sg.org or "general")
        if key in skill_map:
            existing = skill_map[key]
            existing_skills = {s.lower() for s in existing.tags.skills}
            for skill in sg.tags.skills:
                if skill.lower() not in existing_skills:
                    existing.tags.skills.append(skill)
                    existing_skills.add(skill.lower())
            if len(sg.text) > len(existing.text):
                existing.text = sg.text
        else:
            skill_map[key] = sg
    kept.extend(skill_map.values())

    # --- Other units: group by (section, org, role) for efficient comparison ---
    groups: dict[str, list[AtomicUnit]] = {}
    for u in other_units:
        key = (
            f"{u.section.value}|"
            f"{_normalize_text(u.org or '')}|"
            f"{_normalize_text(u.role or '')}"
        )
        groups.setdefault(key, []).append(u)

    for group in groups.values():
        unique: list[AtomicUnit] = []
        for candidate in group:
            is_dup = False
            for i, existing in enumerate(unique):
                sim = _text_similarity(candidate.text, existing.text)
                if sim >= _DEDUP_SIMILARITY_THRESHOLD:
                    # Keep the longer / more detailed version
                    if len(candidate.text) > len(existing.text):
                        unique[i] = candidate
                    is_dup = True
                    break
            if not is_dup:
                unique.append(candidate)
        kept.extend(unique)

    removed = len(all_units) - len(kept)
    return kept, removed


async def ingest_pdf(pdf_content: bytes, filename: str) -> MasterResumeResponse:
    """
    Ingest a single PDF resume and extract atomic units.

    1. Extract text from PDF using PyMuPDF
    2. Send to Gemini for atomic unit extraction
    3. Store in MongoDB with version tracking
    4. Return structured response
    """
    content_hash = hashlib.sha256(pdf_content).hexdigest()[:12]
    version_id = f"master_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{content_hash}"

    full_text = _extract_text_from_pdf(pdf_content)

    if not full_text.strip():
        return MasterResumeResponse(
            master_version_id=version_id,
            atomic_units=[],
            counts={},
            warnings=["Could not extract text from PDF. The file may be scanned/image-based."],
        )

    prompt = EXTRACTION_PROMPT + full_text
    try:
        raw_units = await generate_json(prompt)
    except Exception as e:
        return MasterResumeResponse(
            master_version_id=version_id,
            atomic_units=[],
            counts={},
            warnings=[f"Gemini extraction failed: {str(e)}"],
        )

    atomic_units, warnings = _parse_raw_units(raw_units, filename, version_id)

    counts: dict[str, int] = {}
    for unit in atomic_units:
        section_key = unit.section.value
        counts[section_key] = counts.get(section_key, 0) + 1

    db = await get_database()

    master_version = MasterVersion(
        master_version_id=version_id,
        source_type="pdf",
        source_hash=f"sha256:{content_hash}",
        source_files=[filename],
        atomic_unit_count=len(atomic_units),
        notes=f"Ingested from {filename}",
    )
    await db.master_versions.insert_one(master_version.model_dump())

    if atomic_units:
        await db.atomic_units.insert_many([u.model_dump() for u in atomic_units])

    return MasterResumeResponse(
        master_version_id=version_id, atomic_units=atomic_units, counts=counts, warnings=warnings
    )


async def ingest_multiple_pdfs(
    files: list[tuple[bytes, str]],
) -> MasterResumeResponse:
    """
    Ingest multiple PDF resumes, deduplicate, and merge into one master version.

    Each entry in *files* is (pdf_bytes, filename).

    Steps:
      1. Extract text & parse units from each PDF independently.
      2. Deduplicate across all files (exact + near-duplicate removal).
      3. Re-assign IDs so they are unique within the merged set.
      4. Store the merged master version + units in MongoDB.
    """
    combined_hash = hashlib.sha256(b"".join(content for content, _ in files)).hexdigest()[:12]
    version_id = f"master_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{combined_hash}"

    all_units: list[AtomicUnit] = []
    all_warnings: list[str] = []
    filenames: list[str] = []
    per_file_counts: dict[str, int] = {}
    id_offset = 0

    for pdf_content, filename in files:
        filenames.append(filename)

        full_text = _extract_text_from_pdf(pdf_content)
        if not full_text.strip():
            all_warnings.append(f"{filename}: Could not extract text (scanned/image-based?).")
            per_file_counts[filename] = 0
            continue

        prompt = EXTRACTION_PROMPT + full_text
        try:
            raw_units = await generate_json(prompt)
        except Exception as e:
            all_warnings.append(f"{filename}: Gemini extraction failed: {e}")
            per_file_counts[filename] = 0
            continue

        units, warnings = _parse_raw_units(raw_units, filename, version_id, id_offset)
        per_file_counts[filename] = len(units)
        id_offset += len(units)

        all_units.extend(units)
        all_warnings.extend(warnings)

    total_before = len(all_units)

    # Deduplicate across all files
    merged_units, duplicates_removed = _deduplicate_units(all_units)

    if duplicates_removed > 0:
        all_warnings.append(
            f"Removed {duplicates_removed} duplicate/near-duplicate unit(s) across files."
        )

    # Re-assign sequential IDs so they're clean and unique
    for i, unit in enumerate(merged_units):
        org_slug = "".join(c for c in (unit.org or "unknown")[:10].lower() if c.isalnum())
        unit.id = f"{unit.section.value[:3]}_{org_slug}_{i:03d}"

    counts: dict[str, int] = {}
    for unit in merged_units:
        section_key = unit.section.value
        counts[section_key] = counts.get(section_key, 0) + 1

    merge_stats = MergeStats(
        files_processed=len(files),
        total_units_before_dedup=total_before,
        duplicates_removed=duplicates_removed,
        final_unit_count=len(merged_units),
        per_file_counts=per_file_counts,
    )

    # Persist to MongoDB
    db = await get_database()

    master_version = MasterVersion(
        master_version_id=version_id,
        source_type="multi_pdf",
        source_hash=f"sha256:{combined_hash}",
        source_files=filenames,
        atomic_unit_count=len(merged_units),
        notes=f"Combined from {len(files)} file(s): {', '.join(filenames)}",
    )
    await db.master_versions.insert_one(master_version.model_dump())

    if merged_units:
        await db.atomic_units.insert_many([u.model_dump() for u in merged_units])

    return MasterResumeResponse(
        master_version_id=version_id,
        atomic_units=merged_units,
        counts=counts,
        warnings=all_warnings,
        merge_stats=merge_stats,
    )
