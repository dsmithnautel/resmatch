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
    # RenderCV expects specific keys for social networks
    social_networks = []

    if header_info.get("linkedin"):
        social_networks.append(
            {
                "network": "LinkedIn",
                "username": header_info.get("linkedin", "")
                .split("linkedin.com/in/")[-1]
                .replace("/", ""),
                "url": header_info.get("linkedin"),
            }
        )

    if header_info.get("github"):
        social_networks.append(
            {
                "network": "GitHub",
                "username": header_info.get("github", "").split("github.com/")[-1].replace("/", ""),
                "url": header_info.get("github"),
            }
        )

    cv_header = {
        "name": header_info.get("name", "Your Name"),
        "location": "City, State",  # Placeholder or extract if available
        "email": header_info.get("email"),
        "phone": header_info.get("phone"),
        "social_networks": social_networks,
    }
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
    sections_data = {}

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
            "theme": "sb2nov",
            "font": "Latin Modern Serif",
            "font_size": "10pt",
            "page_size": "letterpaper",
            "color": "#000000",
        },
    }

    return model


def _build_education(units: list[ScoredUnit]) -> list[dict[str, Any]]:
    entries = []
    for unit in units:
        # Assuming one unit per degree for now, strictly speaking atomic units might be granular.
        # But our ingestion usually keeps education entries as blocks or single lines.
        # If granular, we'd need grouping logic. assuming 1 unit = 1 entry for simplicitly first.

        date_str = _format_dates(unit)

        entry = {
            "institution": unit.org or "University",
            "area": unit.role or "Degree",
            "date": date_str,
            # "location": "City, State", # Missing in our extraction
        }
        if unit.text and len(unit.text) > 50:
            # Treat long text as highlights? Or simplified
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

        # Get dates from first bullet
        date_str = _format_dates(bullets[0])

        highlights = [b.text for b in bullets if b.text.strip()]

        entry = {"company": org, "position": role, "date": date_str, "highlights": highlights}
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
            # Fallback to role if org missing
            real_name = bullets[0].role
        else:
            real_name = name

        date_str = _format_dates(bullets[0])
        highlights = [b.text for b in bullets if b.text.strip()]

        # Extract tools from tags
        tools = []
        if bullets[0].tags and isinstance(bullets[0].tags, dict):
            tools = bullets[0].tags.get("skills", [])[:6]  # Limit

        entry = {
            "name": real_name,
            "date": date_str,
            "highlights": highlights,
        }
        if tools:
            entry["tools"] = tools

        entries.append(entry)
    return entries


def _build_skills(units: list[ScoredUnit]) -> list[dict[str, Any]]:
    # RenderCV expects a list of generic objects for this?
    # Actually sb2nov theme expects a specific structure for skills:
    # label: details

    all_skills = []
    for u in units:
        if u.tags and isinstance(u.tags, dict):
            all_skills.extend(u.tags.get("skills", []))

    # De-duplicate
    unique = sorted(set(all_skills))

    # Categorize
    categories = {
        "Languages": [
            "Python",
            "Java",
            "C++",
            "JavaScript",
            "TypeScript",
            "SQL",
            "Go",
            "Rust",
            "Swift",
            "Kotlin",
            "R",
            "MATLAB",
            "HTML",
            "CSS",
        ],
        "Frameworks": [
            "React",
            "Node.js",
            "Flask",
            "Django",
            "FastAPI",
            "Spring",
            "Express",
            "Vue",
            "Angular",
            "Next.js",
            "Torch",
            "PyTorch",
            "TensorFlow",
        ],
        "Tools": [
            "Git",
            "Docker",
            "Kubernetes",
            "AWS",
            "GCP",
            "Azure",
            "MongoDB",
            "PostgreSQL",
            "Redis",
            "Jira",
            "Linux",
            "Unix",
        ],
    }

    final_skills = []

    # Bucket skills
    for cat, keywords in categories.items():
        matches = [s for s in unique if s in keywords]
        if matches:
            final_skills.append({"label": cat, "details": ", ".join(matches)})
            # Remove from pool
            unique = [s for s in unique if s not in matches]

    # Remainder
    if unique:
        final_skills.append({"label": "Other", "details": ", ".join(unique[:10])})

    return final_skills


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
