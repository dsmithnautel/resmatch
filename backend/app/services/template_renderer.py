"""Populate Jake's Resume template with atomic units and compile to PDF."""

import os
import subprocess
import tempfile
from collections import defaultdict

from app.models import ScoredUnit


def load_template() -> str:
    """Load Jake's Resume LaTeX template."""
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "jakes_resume.tex")
    with open(template_path, encoding="utf-8") as f:
        return f.read()


def populate_template(selected_units: list[ScoredUnit], header_info: dict | None = None) -> str:
    """
    Fill Jake's template with selected atomic units.

    Args:
        selected_units: AI-selected bullets
        header_info: Name, email, phone, etc.

    Returns:
        Complete LaTeX source ready to compile
    """
    template = load_template()

    # Extract header info with defaults
    name = "Your Name"
    phone = "123-456-7890"
    email = "email@example.com"
    linkedin = "https://linkedin.com/in/yourname"
    linkedin_display = "linkedin.com/in/yourname"
    github = "https://github.com/yourname"
    github_display = "github.com/yourname"

    if header_info:
        name = header_info.get("name", name)
        phone = header_info.get("phone", phone)
        email = header_info.get("email", email)
        linkedin = header_info.get("linkedin", linkedin)
        github = header_info.get("github", github)
        # Extract display names from URLs
        if "linkedin.com" in linkedin:
            linkedin_display = (
                linkedin.split("linkedin.com/")[-1] if "/" in linkedin else linkedin_display
            )
        if "github.com" in github:
            github_display = github.split("github.com/")[-1] if "/" in github else github_display

    template = template.replace("{{NAME}}", escape_latex(name))
    template = template.replace("{{PHONE}}", escape_latex(phone))
    template = template.replace("{{EMAIL}}", escape_latex(email))
    template = template.replace("{{LINKEDIN}}", linkedin)
    template = template.replace("{{LINKEDIN_DISPLAY}}", escape_latex(linkedin_display))
    template = template.replace("{{GITHUB}}", github)
    template = template.replace("{{GITHUB_DISPLAY}}", escape_latex(github_display))

    # Group units by section
    sections = defaultdict(list)
    for unit in selected_units:
        # Section is already a string, not an enum
        section_name = unit.section if isinstance(unit.section, str) else unit.section.value
        sections[section_name].append(unit)

    # Build sections
    education_latex = build_education_section(sections.get("education", []))
    template = template.replace("{{EDUCATION_ENTRIES}}", education_latex)

    experience_latex = build_experience_section(sections.get("experience", []))
    template = template.replace("{{EXPERIENCE_ENTRIES}}", experience_latex)

    projects_latex = build_projects_section(sections.get("projects", []))
    template = template.replace("{{PROJECT_ENTRIES}}", projects_latex)

    skills_latex = build_skills_section(sections.get("skills", []))
    template = template.replace("{{SKILLS_ENTRIES}}", skills_latex)

    return template


def build_education_section(units: list[ScoredUnit]) -> str:
    """Build education section in Jake's format."""
    if not units:
        return ""

    latex = ""
    for unit in units:
        org = escape_latex(unit.org or "University")
        role = escape_latex(unit.role or "Degree")

        # Format dates (if available)
        dates = ""
        unit_dates = getattr(unit, "dates", None)
        if unit_dates:
            start = getattr(unit_dates, "start", "") or ""
            end = getattr(unit_dates, "end", "") or ""
            dates = f"{start} -- {end}"

        latex += f"""    \\resumeSubheading
      {{{org}}}{{}}
      {{{role}}}{{{dates}}}
"""

    return latex


def build_experience_section(units: list[ScoredUnit]) -> str:
    """Build experience section with bullets grouped by company."""
    if not units:
        return ""

    # Group by company + role
    grouped = defaultdict(list)
    for unit in units:
        key = f"{unit.org or 'Company'}|{unit.role or 'Position'}"
        grouped[key].append(unit)

    latex = ""
    for key, bullets in grouped.items():
        org, role = key.split("|")
        org = escape_latex(org)
        role = escape_latex(role)

        # Get dates from first bullet (if available)
        dates = ""
        unit_dates = getattr(bullets[0], "dates", None)
        if unit_dates:
            start = getattr(unit_dates, "start", "") or ""
            end = getattr(unit_dates, "end", "") or "Present"
            dates = f"{start} -- {end}"

        latex += f"""
    \\resumeSubheading
      {{{role}}}{{{dates}}}
      {{{org}}}{{}}
      \\resumeItemListStart
"""

        # Add bullets
        for bullet in bullets:
            text = escape_latex(bullet.text)
            latex += f"        \\resumeItem{{{text}}}\n"

        latex += "      \\resumeItemListEnd\n"

    return latex


def build_projects_section(units: list[ScoredUnit]) -> str:
    """Build projects section."""
    if not units:
        return ""

    # Group by project name
    grouped = defaultdict(list)
    for unit in units:
        project_name = unit.org or "Project"
        grouped[project_name].append(unit)

    latex = ""
    for project_name, bullets in grouped.items():
        project_name = escape_latex(project_name)

        # Extract tech stack from tags (if available)
        tech_stack = "Technologies"
        if bullets[0].tags and isinstance(bullets[0].tags, dict):
            skills = bullets[0].tags.get("skills", [])
            if skills:
                tech_stack = ", ".join(skills[:5])

        # Get dates (if available)
        dates = ""
        unit_dates = getattr(bullets[0], "dates", None)
        if unit_dates:
            start = getattr(unit_dates, "start", "") or ""
            end = getattr(unit_dates, "end", "") or "Present"
            dates = f"{start} -- {end}"

        latex += f"""      \\resumeProjectHeading
          {{\\textbf{{{project_name}}} $|$ \\emph{{{tech_stack}}}}}{{{dates}}}
          \\resumeItemListStart
"""

        for bullet in bullets:
            text = escape_latex(bullet.text)
            latex += f"            \\resumeItem{{{text}}}\n"

        latex += "          \\resumeItemListEnd\n"

    return latex


def build_skills_section(units: list[ScoredUnit]) -> str:
    """Build technical skills section."""
    if not units:
        # Return default skills if none provided
        return """     \\textbf{Languages}{: Python, Java, JavaScript} \\\\
     \\textbf{Frameworks}{: React, Flask, FastAPI} \\\\
     \\textbf{Developer Tools}{: Git, Docker, AWS}"""

    # Aggregate all skills from tags (if available)
    all_skills: list[str] = []
    for unit in units:
        unit_tags = getattr(unit, "tags", None)
        if unit_tags:
            skills = getattr(unit_tags, "skills", [])
            if skills:
                all_skills.extend(skills)

    # Remove duplicates, preserve order
    seen = set()
    unique_skills = []
    for skill in all_skills:
        if skill.lower() not in seen:
            seen.add(skill.lower())
            unique_skills.append(skill)

    # Categorize skills (simple heuristic)
    languages = [
        s
        for s in unique_skills
        if s
        in [
            "Python",
            "Java",
            "C++",
            "C",
            "JavaScript",
            "TypeScript",
            "SQL",
            "Go",
            "Rust",
            "Ruby",
            "PHP",
            "Swift",
            "Kotlin",
            "R",
        ]
    ]
    frameworks = [
        s
        for s in unique_skills
        if s
        in [
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
            "Rails",
        ]
    ]
    tools = [
        s
        for s in unique_skills
        if s
        in [
            "Git",
            "Docker",
            "Kubernetes",
            "AWS",
            "GCP",
            "Azure",
            "MongoDB",
            "PostgreSQL",
            "Redis",
            "Jenkins",
            "CI/CD",
        ]
    ]

    # Build LaTeX
    latex_parts = []
    if languages:
        latex_parts.append(f"\\textbf{{Languages}}{{: {', '.join(languages)}}}")
    if frameworks:
        latex_parts.append(f"\\textbf{{Frameworks}}{{: {', '.join(frameworks)}}}")
    if tools:
        latex_parts.append(f"\\textbf{{Developer Tools}}{{: {', '.join(tools)}}}")

    # If no categorized skills, just list all
    if not latex_parts and unique_skills:
        latex_parts.append(f"\\textbf{{Skills}}{{: {', '.join(unique_skills[:15])}}}")

    return (
        " \\\\\n     ".join(latex_parts)
        if latex_parts
        else "\\textbf{Skills}{: Python, JavaScript, Git}"
    )


def escape_latex(text: str) -> str:
    """Escape special LaTeX characters."""
    if not text:
        return ""

    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }

    # Process backslash first
    result = text.replace("\\", replacements["\\"])
    # Then process other characters
    for char, replacement in replacements.items():
        if char != "\\":
            result = result.replace(char, replacement)

    return result


async def compile_latex_to_pdf(latex_source: str, output_path: str) -> str:
    """
    Compile LaTeX to PDF using pdflatex.

    Args:
        latex_source: Complete LaTeX source code
        output_path: Where to save the PDF

    Returns:
        Path to generated PDF

    Raises:
        RuntimeError: If compilation fails
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write LaTeX source
        tex_path = os.path.join(tmpdir, "resume.tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_source)

        # Compile with pdflatex (run twice for references)
        for _ in range(2):
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "resume.tex"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=30,
            )

        # Check if PDF was generated
        pdf_path = os.path.join(tmpdir, "resume.pdf")
        if os.path.exists(pdf_path):
            import shutil

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            shutil.copy(pdf_path, output_path)
            return output_path
        else:
            # Compilation failed - try to extract error
            log_path = os.path.join(tmpdir, "resume.log")
            error_msg = "LaTeX compilation failed"
            if os.path.exists(log_path):
                with open(log_path) as f:
                    log_content = f.read()
                    # Extract first error line
                    for line in log_content.split("\n"):
                        if line.startswith("!"):
                            error_msg += f": {line}"
                            break
            raise RuntimeError(error_msg)
