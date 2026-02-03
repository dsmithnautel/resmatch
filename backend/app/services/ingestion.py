"""PDF ingestion service - extracts atomic units from master resume."""

import hashlib
from datetime import datetime

import fitz  # PyMuPDF

from app.db.mongodb import get_database
from app.models import AtomicUnit, MasterResumeResponse, MasterVersion
from app.models.atomic_unit import AtomicUnitType, DateRange, Evidence, SectionType, Tags
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


async def ingest_pdf(pdf_content: bytes, filename: str) -> MasterResumeResponse:
    """
    Ingest a PDF resume and extract atomic units.

    1. Extract text from PDF using PyMuPDF
    2. Send to Gemini for atomic unit extraction
    3. Store in MongoDB with version tracking
    4. Return structured response
    """
    # Generate version ID
    content_hash = hashlib.sha256(pdf_content).hexdigest()[:12]
    # Add timestamp to allow multiple uploads of same file for debugging
    version_id = f"master_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{content_hash}"

    # Extract text from PDF
    doc = fitz.open(stream=pdf_content, filetype="pdf")
    full_text = ""
    for page_num, page in enumerate(doc):
        text = page.get_text()
        # Basic cleaning: remove null bytes and normalize whitespace
        text = text.replace("\0", "").strip()
        if text:
            full_text += f"\n--- Page {page_num + 1} ---\n"
            full_text += text
    doc.close()

    if not full_text.strip():
        return MasterResumeResponse(
            master_version_id=version_id,
            atomic_units=[],
            counts={},
            warnings=["Could not extract text from PDF. The file may be scanned/image-based."],
        )

    # Extract atomic units using Gemini
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

    # Parse and validate units
    atomic_units = []
    warnings = []
    counts = {}

    for i, raw in enumerate(raw_units):
        try:
            # Normalize section - map variations to standard names
            raw_section = raw.get("section", "experience").lower()
            normalized_section = SECTION_MAPPING.get(raw_section, raw_section)

            # Fall back to 'other' if section is completely unknown
            # This preserves unrecognized sections instead of losing context
            valid_sections = [s.value for s in SectionType]
            if normalized_section not in valid_sections:
                normalized_section = "other"
                warnings.append(f"Unit {i}: Unknown section '{raw_section}' mapped to 'other'")

            # Generate unique ID
            org = raw.get("org", "unknown")
            org_slug = "".join(c for c in (org or "unknown")[:10].lower() if c.isalnum())
            unit_id = f"{normalized_section[:3]}_{org_slug}_{i:03d}"

            # Parse dates
            dates = None
            if raw.get("dates"):
                dates = DateRange(start=raw["dates"].get("start"), end=raw["dates"].get("end"))

            # Parse tags
            tags = Tags(
                skills=raw.get("tags", {}).get("skills", []),
                domains=raw.get("tags", {}).get("domains", []),
                seniority=raw.get("tags", {}).get("seniority"),
                # Contact info (from header units)
                email=raw.get("tags", {}).get("email"),
                phone=raw.get("tags", {}).get("phone"),
                linkedin=raw.get("tags", {}).get("linkedin"),
                github=raw.get("tags", {}).get("github"),
            )

            # Normalize type - map invalid types to valid ones
            raw_type = raw.get("type", "bullet").lower()
            normalized_type = TYPE_MAPPING.get(raw_type, "bullet")

            # Create atomic unit
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

            # Count by section
            section_key = unit.section.value
            counts[section_key] = counts.get(section_key, 0) + 1

        except Exception as e:
            warnings.append(f"Failed to parse unit {i}: {str(e)}")

    # Store in MongoDB
    db = await get_database()

    # Store version metadata
    master_version = MasterVersion(
        master_version_id=version_id,
        source_type="pdf",
        source_hash=f"sha256:{content_hash}",
        atomic_unit_count=len(atomic_units),
        notes=f"Ingested from {filename}",
    )
    await db.master_versions.insert_one(master_version.model_dump())

    # Store atomic units
    if atomic_units:
        await db.atomic_units.insert_many([u.model_dump() for u in atomic_units])

    return MasterResumeResponse(
        master_version_id=version_id, atomic_units=atomic_units, counts=counts, warnings=warnings
    )
