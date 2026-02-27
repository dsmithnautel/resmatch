"""
Deterministic LaTeX generator for Jake's Resume template.

Produces a complete .tex file from structured resume data,
using pure string formatting — no LLM involved.
"""

import re


def _escape_latex(text: str) -> str:
    """Escape special LaTeX characters in user text."""
    # Order matters: & must be before \
    replacements = [
        ("\\", "\\textbackslash{}"),
        ("&", "\\&"),
        ("%", "\\%"),
        ("$", "\\$"),
        ("#", "\\#"),
        ("_", "\\_"),
        ("{", "\\{"),
        ("}", "\\}"),
        ("~", "\\textasciitilde{}"),
        ("^", "\\textasciicircum{}"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _format_dates(dates: dict | str | None) -> str:
    """Convert dates dict to LaTeX-friendly string like 'May 2025 -- Aug. 2025'."""
    if not dates:
        return ""
    if isinstance(dates, str):
        return _escape_latex(dates)

    months = [
        "", "Jan.", "Feb.", "Mar.", "Apr.", "May", "June",
        "July", "Aug.", "Sep.", "Oct.", "Nov.", "Dec.",
    ]

    def fmt(d: str | None) -> str:
        if not d:
            return ""
        parts = d.split("-")
        if len(parts) == 2:
            m = int(parts[1])
            return f"{months[m]} {parts[0]}"
        return d

    start = fmt(dates.get("start"))
    end = fmt(dates.get("end")) if dates.get("end") else "Present"
    if start and end:
        return f"{start} -- {end}"
    return start or end


# ── Preamble (identical to JAKES_TEMPLATE but without \input{glyphtounicode}) ──

PREAMBLE = r"""\documentclass[letterpaper,11pt]{article}

\usepackage{latexsym}
\usepackage[margin=0.5in]{geometry}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}


\pagestyle{empty}
\urlstyle{same}

\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

% Sections formatting
\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

%-------------------------
% Custom commands
\newcommand{\resumeItem}[1]{
  \item\small{
    {#1 \vspace{-2pt}}
  }
}

\newcommand{\resumeSubheading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubSubheading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \textit{\small#1} & \textit{\small #2} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeProjectHeading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \small#1 & #2 \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubItem}[1]{\resumeItem{#1}\vspace{-4pt}}

\renewcommand\labelitemii{$\vcenter{\hbox{\tiny$\bullet$}}$}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

"""


def generate_latex(
    header: dict,
    units: list[dict],
) -> str:
    """
    Generate a complete LaTeX document from header info + flat list of units.

    Args:
        header: {name, email, phone, linkedin, github}
        units: list of dicts with keys: text, section, org, role, dates
    """
    # Group units by section, preserving order
    from collections import OrderedDict

    sections: OrderedDict[str, list[dict]] = OrderedDict()
    for u in units:
        sec = (u.get("section") or "other").lower()
        if sec not in sections:
            sections[sec] = []
        sections[sec].append(u)

    parts = [PREAMBLE, "\\begin{document}\n"]

    # ── Header ──
    name = _escape_latex(header.get("name", "Your Name"))
    phone = _escape_latex(header.get("phone", ""))
    email = header.get("email", "")
    linkedin = header.get("linkedin", "")
    github = header.get("github", "")

    parts.append("\\begin{center}\n")
    parts.append(f"    \\textbf{{\\Huge \\scshape {name}}} \\\\ \\vspace{{1pt}}\n")

    contact_parts = []
    if phone:
        contact_parts.append(f"\\small {phone}")
    if email:
        contact_parts.append(
            f"\\href{{mailto:{email}}}{{\\underline{{{_escape_latex(email)}}}}}"
        )
    if linkedin:
        url = linkedin if linkedin.startswith("http") else f"https://{linkedin}"
        display = re.sub(r"^https?://", "", linkedin)
        contact_parts.append(
            f"\\href{{{url}}}{{\\underline{{{_escape_latex(display)}}}}}"
        )
    if github:
        url = github if github.startswith("http") else f"https://{github}"
        display = re.sub(r"^https?://", "", github)
        contact_parts.append(
            f"\\href{{{url}}}{{\\underline{{{_escape_latex(display)}}}}}"
        )

    parts.append("    " + " $|$ ".join(contact_parts) + "\n")
    parts.append("\\end{center}\n\n")

    # ── Render each section ──
    section_order = ["education", "experience", "projects", "leadership", "skills"]
    # Include any sections not in the standard order
    for sec in sections:
        if sec not in section_order:
            section_order.append(sec)

    for sec_name in section_order:
        if sec_name not in sections:
            continue
        sec_units = sections[sec_name]

        # Section title
        title = sec_name.replace("_", " ").title()
        if sec_name == "skills":
            title = "Technical Skills"

        if sec_name == "skills":
            parts.append(_render_skills_section(title, sec_units))
        elif sec_name == "projects":
            parts.append(_render_projects_section(title, sec_units))
        elif sec_name in ("experience", "leadership"):
            parts.append(_render_experience_section(title, sec_units))
        elif sec_name == "education":
            parts.append(_render_education_section(title, sec_units))
        else:
            parts.append(_render_experience_section(title, sec_units))

    parts.append("\\end{document}\n")
    return "".join(parts)


def _group_by_org_role(units: list[dict]) -> list[dict]:
    """Group flat units into entries by (org, role)."""
    entries: list[dict] = []
    for u in units:
        org = u.get("org") or ""
        role = u.get("role") or ""
        dates = u.get("dates")

        # Check if last entry has same org+role
        if entries and entries[-1]["org"] == org and entries[-1]["role"] == role:
            entries[-1]["bullets"].append(u.get("text", ""))
        else:
            entries.append({
                "org": org,
                "role": role,
                "dates": dates,
                "bullets": [u.get("text", "")],
            })
    return entries


def _render_experience_section(title: str, units: list[dict]) -> str:
    """Render experience/leadership section with \\resumeSubheading."""
    entries = _group_by_org_role(units)
    lines = [f"\\section{{{title}}}\n", "  \\resumeSubHeadingListStart\n"]

    for entry in entries:
        role = _escape_latex(entry["role"])
        org = _escape_latex(entry["org"])
        dates = _format_dates(entry["dates"])

        lines.append(f"\n    \\resumeSubheading\n")
        lines.append(f"      {{{role}}}{{{dates}}}\n")
        lines.append(f"      {{{org}}}{{}}\n")

        if entry["bullets"]:
            lines.append("      \\resumeItemListStart\n")
            for bullet in entry["bullets"]:
                lines.append(f"        \\resumeItem{{{_escape_latex(bullet)}}}\n")
            lines.append("      \\resumeItemListEnd\n")

    lines.append("\n  \\resumeSubHeadingListEnd\n\n")
    return "".join(lines)


def _render_education_section(title: str, units: list[dict]) -> str:
    """Render education section with \\resumeSubheading."""
    entries = _group_by_org_role(units)
    lines = [f"\\section{{{title}}}\n", "  \\resumeSubHeadingListStart\n"]

    for entry in entries:
        org = _escape_latex(entry["org"])
        role = _escape_latex(entry["role"])
        dates = _format_dates(entry["dates"])

        if org:
            # Education: org=school (bold), role=degree (italic)
            lines.append(f"    \\resumeSubheading\n")
            lines.append(f"      {{{org}}}{{}}\n")
            lines.append(f"      {{{role}}}{{{dates}}}\n")

            if entry["bullets"]:
                lines.append("      \\resumeItemListStart\n")
                for bullet in entry["bullets"]:
                    lines.append(f"        \\resumeItem{{{_escape_latex(bullet)}}}\n")
                lines.append("      \\resumeItemListEnd\n")
        else:
            # No org — render bullets as standalone items
            for bullet in entry["bullets"]:
                lines.append(f"    \\resumeSubItem{{{_escape_latex(bullet)}}}\n")

    lines.append("  \\resumeSubHeadingListEnd\n\n")
    return "".join(lines)


def _render_projects_section(title: str, units: list[dict]) -> str:
    """Render projects section with \\resumeProjectHeading."""
    lines = [f"\\section{{{title}}}\n", "    \\resumeSubHeadingListStart\n"]

    # Projects: header entries have org set, bullet entries don't
    current_project: str | None = None
    bullets: list[str] = []

    def flush():
        nonlocal current_project, bullets
        if current_project is not None:
            lines.append(f"      \\resumeProjectHeading\n")
            lines.append(
                f"          {{\\textbf{{{_escape_latex(current_project)}}}}}{{}}\n"
            )
            if bullets:
                lines.append("          \\resumeItemListStart\n")
                for b in bullets:
                    lines.append(f"            \\resumeItem{{{_escape_latex(b)}}}\n")
                lines.append("          \\resumeItemListEnd\n")
        bullets = []

    for u in units:
        org = u.get("org")
        text = u.get("text", "")

        if org:
            # This is a project header
            flush()
            current_project = org
        else:
            # This is a bullet
            bullets.append(text)

    flush()
    lines.append("    \\resumeSubHeadingListEnd\n\n")
    return "".join(lines)


def _render_skills_section(title: str, units: list[dict]) -> str:
    """Render technical skills section."""
    lines = [
        f"\\section{{{title}}}\n",
        " \\begin{itemize}[leftmargin=0.15in, label={}]\n",
        "    \\small{\\item{\n",
    ]

    skill_lines = []
    for u in units:
        text = u.get("text", "")
        colon_idx = text.find(":")
        if colon_idx > 0:
            category = _escape_latex(text[:colon_idx].strip())
            skills = _escape_latex(text[colon_idx + 1 :].strip())
            skill_lines.append(f"     \\textbf{{{category}}}{{: {skills}}}")
        else:
            skill_lines.append(f"     {_escape_latex(text)}")

    lines.append(" \\\\\n".join(skill_lines) + "\n")
    lines.append("    }}\n")
    lines.append(" \\end{itemize}\n\n")
    return "".join(lines)
