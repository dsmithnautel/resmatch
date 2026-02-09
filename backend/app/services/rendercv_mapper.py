"""
Mapper service to convert internal Atomic Units to RenderCV data model.
Target Theme: sb2nov (Jake's Resume)
"""

from collections import defaultdict
from typing import Any

from app.models import ScoredUnit


def map_to_rendercv_model(units: list[ScoredUnit], header_info: dict[str, str]) -> dict[str, Any]:
    """
    Convert flat list of units + header dict into RenderCV data model.
    """

    # 1. Construct Header
    # RenderCV 2.x handles standard social networks as top-level keys
    # Calculate phone first to match RenderCV format
    raw_phone = str(header_info.get("phone", ""))
    digits = "".join(filter(str.isdigit, raw_phone))
    if len(digits) == 10:
        phone_val = f"+1 {digits}"
    else:
        phone_val = raw_phone

    cv_header = {
        "name": header_info.get("name", "Your Name"),
        "location": "City, State",
        "email": header_info.get("email") or "contact@example.com",  # Fallback for validation
        "phone": phone_val
        if phone_val and phone_val != ""
        else "+1 000-000-0000",  # Fallback for validation
    }
    # Add optional top-level links
    if header_info.get("linkedin"):
        cv_header["linkedin"] = header_info["linkedin"]

    if header_info.get("github"):
        cv_header["github"] = header_info["github"]

    # 2. Group Sections
    # We group units by section, then by entry (Company/Project)
    grouped_sections: dict[str, list[ScoredUnit]] = defaultdict(list)
    for unit in units:
        # Normalize section name
        sec = unit.section.lower()
        if sec not in grouped_sections:
            grouped_sections[sec] = []
        grouped_sections[sec].append(unit)

    # 3. Build Section Content
    sections_data: dict[str, Any] = {}

    # -- Education --
    if "education" in grouped_sections:
        sections_data["education"] = _build_education(grouped_sections["education"])

    # -- Experience --
    if "experience" in grouped_sections:
        sections_data["experience"] = _build_experience(grouped_sections["experience"])

    # -- Projects --
    if "projects" in grouped_sections:
        sections_data["projects"] = _build_projects(grouped_sections["projects"])

    # -- Leadership/Volunteering --
    # RenderCV allows arbitrary sections. We map "leadership" directly.
    if "leadership" in grouped_sections:
        sections_data["leadership"] = _build_experience(
            grouped_sections["leadership"]
        )  # Re-use exp structure

    # -- Skills --
    if "skills" in grouped_sections:
        sections_data["technical_skills"] = _build_skills(grouped_sections["skills"])

    # 4. Construct Final YAML Structure
    # Order matters for RenderCV sections list
    section_order = ["education", "experience", "projects", "leadership", "technical_skills"]
    final_sections = {k: sections_data[k] for k in section_order if k in sections_data}

    model = {
        "cv": {**cv_header, "sections": final_sections},
        "design": {
            "theme": "sb2nov"
            # Note: font and font_size are not valid in RenderCV 2.x design schema
            # Theme controls all typography settings
        },
    }

    return model


def _build_education(units: list[ScoredUnit]) -> list[dict[str, Any]]:
    entries = []
    for unit in units:
        # Assuming one unit per degree for now
        date_str = _format_dates(unit)

        entry = {
            "institution": unit.org or "University",
            "area": unit.role or "Degree",
            "date": date_str,
        }
        if unit.text and len(unit.text) > 50:
            pass
        entries.append(entry)
    return entries


def _build_experience(units: list[ScoredUnit]) -> list[dict[str, Any]]:
    # Group by Organization + Role
    grouped = defaultdict(list)
    for unit in units:
        key = f"{unit.org or 'Company'}|{unit.role or 'Position'}"
        grouped[key].append(unit)

    entries = []
    for key, bullets in grouped.items():
        org, role = key.split("|")
        date_str = _format_dates(bullets[0])
        highlights = [b.text for b in bullets if b.text.strip()]

        entry = {
            "company": org,
            "position": role,
            "date": date_str,
            "highlights": highlights,
        }
        entries.append(entry)
    return entries


def _build_projects(units: list[ScoredUnit]) -> list[dict[str, Any]]:
    # Group by Project Name
    grouped = defaultdict(list)
    for unit in units:
        name = unit.org or "Project"
        grouped[name].append(unit)

    entries = []
    for name, bullets in grouped.items():
        if name == "Project" and bullets[0].role:
            real_name = bullets[0].role
        else:
            real_name = name

        date_str = _format_dates(bullets[0])
        highlights = [b.text for b in bullets if b.text.strip()]

        # Extract tools from tags
        tools = []
        if bullets[0].tags and isinstance(bullets[0].tags, dict):
            tools = bullets[0].tags.get("skills", [])[:6]

        entry = {
            "name": real_name,
            "date": date_str,
            "highlights": highlights,
        }
        if tools:
            entry["tools"] = tools

        entries.append(entry)
    return entries


def _build_skills(units: list[ScoredUnit]) -> list[str]:
    """
    Build technical skills section using categories provided by LLM.
    The ingestion prompt now ensures 'org' contains the category name.
    """
    skills_list = []

    for u in units:
        # LLM puts category in 'org' (e.g. "Languages", "Frameworks")
        # If missing, fallback to "Skills"
        category = u.org or "Skills"
        details = u.text or ""

        if details:
            # Format as bolded category + details
            skills_list.append(f"**{category}**: {details}")

    # Remove exact duplicates and sort
    return sorted(set(skills_list))


def _format_dates(unit: ScoredUnit) -> str:
    dates = unit.dates
    if dates and isinstance(dates, dict):
        start = dates.get("start", "") or ""
        end = dates.get("end", "") or "Present"
        if start and end:
            return f"{start} – {end}"
        if start:
            return start
    return "Present"  # Default fallthrough
