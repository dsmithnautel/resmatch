"""PDF ingestion service - extracts atomic units from master resume."""

import hashlib
import uuid
from datetime import datetime
import fitz  # PyMuPDF

from app.models import AtomicUnit, MasterVersion, MasterResumeResponse
from app.models.atomic_unit import AtomicUnitType, SectionType, DateRange, Tags, Evidence
from app.services.gemini import generate_json
from app.db.mongodb import get_database


EXTRACTION_PROMPT = """
You are a resume parser. Extract ALL content from this resume into atomic units.
Each unit is ONE bullet point, skill group, education entry, or project.

Return a JSON array. For EACH unit, include:
{
  "type": "bullet" | "skill_group" | "education" | "project" | "header",
  "section": "experience" | "projects" | "education" | "skills" | "header",
  "org": "company/school name (or null)",
  "role": "job title or degree (or null)",
  "dates": {"start": "YYYY-MM or null", "end": "YYYY-MM or present or null"},
  "text": "EXACT text from resume - DO NOT modify, summarize, or expand",
  "tags": {
    "skills": ["skill1", "skill2", ...],
    "domains": ["backend", "frontend", "ml", "data", "devops", "mobile", etc.],
    "seniority": "intern" | "entry" | "mid" | "senior" | "staff" | null
  }
}

CRITICAL RULES:
1. Use ONLY text that appears VERBATIM in the resume
2. Do NOT infer, expand, or add any information
3. Do NOT merge multiple bullets into one
4. If dates are unclear, use null
5. Extract EVERY bullet point, even short ones
6. For skills section, create one skill_group per category
7. Include header info (name, contact) as type "header"

Resume text:
"""


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
    version_id = f"master_{datetime.now().strftime('%Y%m%d')}_{content_hash}"
    
    # Extract text from PDF
    doc = fitz.open(stream=pdf_content, filetype="pdf")
    full_text = ""
    for page_num, page in enumerate(doc):
        full_text += f"\n--- Page {page_num + 1} ---\n"
        full_text += page.get_text()
    doc.close()
    
    if not full_text.strip():
        return MasterResumeResponse(
            master_version_id=version_id,
            atomic_units=[],
            counts={},
            warnings=["Could not extract text from PDF. The file may be scanned/image-based."]
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
            warnings=[f"Gemini extraction failed: {str(e)}"]
        )
    
    # Parse and validate units
    atomic_units = []
    warnings = []
    counts = {}
    
    # Map invalid types to valid AtomicUnitTypes
    # Gemini sometimes confuses section names with type names
    TYPE_MAPPING = {
        "experience": "bullet",      # Experience items are bullets
        "projects": "project",       # Projects section -> project type
        "skills": "skill_group",     # Skills section -> skill_group type
        "bullet": "bullet",
        "skill_group": "skill_group",
        "education": "education",
        "project": "project",
        "header": "header",
    }
    
    for i, raw in enumerate(raw_units):
        try:
            # Generate unique ID
            section = raw.get("section", "experience")
            org = raw.get("org", "unknown")
            org_slug = "".join(c for c in (org or "unknown")[:10].lower() if c.isalnum())
            unit_id = f"{section[:3]}_{org_slug}_{i:03d}"
            
            # Parse dates
            dates = None
            if raw.get("dates"):
                dates = DateRange(
                    start=raw["dates"].get("start"),
                    end=raw["dates"].get("end")
                )
            
            # Parse tags
            tags = Tags(
                skills=raw.get("tags", {}).get("skills", []),
                domains=raw.get("tags", {}).get("domains", []),
                seniority=raw.get("tags", {}).get("seniority")
            )
            
            # Normalize type - map invalid types to valid ones
            raw_type = raw.get("type", "bullet").lower()
            normalized_type = TYPE_MAPPING.get(raw_type, "bullet")
            
            # Create atomic unit
            unit = AtomicUnit(
                id=unit_id,
                type=AtomicUnitType(normalized_type),
                section=SectionType(raw.get("section", "experience")),
                org=raw.get("org"),
                role=raw.get("role"),
                dates=dates,
                text=raw.get("text", ""),
                tags=tags,
                evidence=Evidence(source=filename, page=1),
                version=version_id
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
        notes=f"Ingested from {filename}"
    )
    await db.master_versions.insert_one(master_version.model_dump())
    
    # Store atomic units
    if atomic_units:
        await db.atomic_units.insert_many([u.model_dump() for u in atomic_units])
    
    return MasterResumeResponse(
        master_version_id=version_id,
        atomic_units=atomic_units,
        counts=counts,
        warnings=warnings
    )
