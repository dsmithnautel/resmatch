"""LLM-based tailoring service for atomic units against job descriptions."""

import json
from typing import Any

from app.models import ParsedJD, ScoredUnit
from app.services.gemini import generate_json

TAILORING_PROMPT = """
You are a professional technical resume writer, ATS optimization expert, and LaTeX resume formatter.

Your task is to tailor the applicant’s resume bullet points to better align with the provided Job Description (JD), while STRICTLY preserving factual accuracy, original intent, and LaTeX compatibility.

════════════════════════════
CORE RULES (NON-NEGOTIABLE)
════════════════════════════
- DO NOT fabricate, exaggerate, infer, or assume any experience not explicitly stated.
- DO NOT add tools, technologies, metrics, scope, seniority, or responsibilities not present in the original bullet.
- DO NOT change timelines, ownership, or level of responsibility.
- DO NOT convert academic, personal, or internship work into professional experience unless explicitly stated.
- DO NOT keyword-stuff or force irrelevant JD terms.
- If a JD requirement is not supported by the bullet, do NOT imply it.

════════════════════════════
FORMATTING & LAYOUT GUARDRAILS
════════════════════════════
- Output bullets MUST fit a 1-page resume using a standard LaTeX resume template.
- Bullets should be concise and dense; prefer removing filler words over adding detail.
- Do NOT increase vertical space usage:
  - Avoid multi-clause sentences.
  - Avoid commas where a tighter phrasing is possible.
  - Avoid unnecessary adjectives or adverbs.
- Length of tailored bullet must remain within ±20% of the original bullet length.
- Each bullet should ideally fit on ONE line in LaTeX when possible.
- Use standard LaTeX-safe characters only.
- DO NOT introduce special characters, emojis, or formatting macros.
- Preserve sentence-style bullets (no trailing periods unless originally present).

════════════════════════════
LATEX-SPECIFIC RULES
════════════════════════════
- Assume bullets are inside a \\resumeItem{} or \\item macro.
- Do NOT escape characters unless necessary for LaTeX compilation.
- Avoid characters that commonly break LaTeX (%, &, #, _, $) unless already present.
- Do NOT introduce inline code formatting or LaTeX commands.
- Do NOT alter capitalization style unless improving clarity.

════════════════════════════
PROCESS (FOR EACH BULLET)
════════════════════════════
For EACH bullet point provided:

1. ANALYZE
   - Identify the core action, tools, and outcome.
   - Identify legitimate overlap with JD requirements or keywords.

2. REWRITE
   Rewrite the bullet to:
   - Start with a strong, precise action verb.
   - Emphasize JD-relevant aspects ONLY where truthful.
   - Improve clarity and impact while minimizing word count.
   - Preserve original scope, claims, and tone.
   - Maintain LaTeX safety and template compatibility.

3. SCORE
   Assign a relevance score (0–10) based on how well the ORIGINAL bullet matches the JD:
   - 0–2: Unrelated or tangential
   - 3–5: Partial or indirect relevance
   - 6–8: Clear relevance to key responsibilities
   - 9–10: Strong alignment with core JD requirements

4. EXPLAIN
   Briefly describe what was changed and why:
   - Reference clarity, conciseness, or JD alignment.
   - Do NOT justify changes with assumptions.
   - If minimal or no changes were made, explicitly state that.

════════════════════════════
JOB DESCRIPTION
════════════════════════════
Company: {company}
Role: {role_title}

Must-Have Requirements:
{must_haves}

Key Responsibilities:
{responsibilities}

Technical Keywords:
{keywords}

════════════════════════════
RESUME BULLETS TO TAILOR
════════════════════════════
{bullets_json}

════════════════════════════
OUTPUT FORMAT (STRICT)
════════════════════════════
Return a JSON array with ONE object per bullet and NO extra text.

Each object MUST follow this schema exactly:
[
  {{
    "id": "bullet_id",
    "original_text": "Exact original bullet text",
    "tailored_text": "Rewritten bullet, LaTeX-safe and 1-page compliant",
    "score": 8.5,
    "changes_made": "Brief, factual explanation of edits"
  }}
]

- Output MUST be valid JSON.
- Preserve bullet order.
- Do NOT include markdown, commentary, or additional fields.
"""


async def tailor_units_against_jd(
    units: list[dict[str, Any]], parsed_jd: ParsedJD
) -> list[ScoredUnit]:
    """
    Tailor atomic units against a job description using Gemini LLM.

    This replaces the pure scoring approach. Now we:
    1. Send units + JD to Gemini
    2. Request REWORDED versions of each bullet
    3. Return ScoredUnit objects containing the tailored text
    """
    # Filter to tailor-able units (bullets, projects)
    # Education usually doesn't need rewriting, but projects/experience do.
    tailorable = [u for u in units if u.get("type") in ["bullet", "project"]]

    # Education and Skill units - pass through as is
    passthrough_units = [u for u in units if u.get("type") in ["education", "skill_group"]]

    if not tailorable and not passthrough_units:
        return []

    tailored_results = []

    # Process tailorable units
    if tailorable:
        # Prepare bullets for the prompt
        bullets_for_prompt = []
        for u in tailorable:
            bullets_for_prompt.append(
                {
                    "id": u.get("id"),
                    "text": u.get("text"),
                    "section": u.get("section"),
                    "org": u.get("org"),  # Context
                    "role": u.get("role"),  # Context
                }
            )

        # Format the prompt
        prompt = TAILORING_PROMPT.format(
            company=parsed_jd.company,
            role_title=parsed_jd.role_title,
            must_haves="\n".join(f"- {req}" for req in parsed_jd.must_haves),
            responsibilities="\n".join(f"- {resp}" for resp in parsed_jd.responsibilities),
            keywords=", ".join(parsed_jd.keywords),
            bullets_json=json.dumps(bullets_for_prompt, indent=2),
        )

        # Get tailored bullets from Gemini
        try:
            tailored_raw = await generate_json(prompt)

            # Map results back to units
            tailored_map = {t["id"]: t for t in tailored_raw}

            for u in tailorable:
                unit_id = u.get("id")
                result = tailored_map.get(unit_id, {})

                # Use tailored text if available, else original
                final_text = result.get("tailored_text", u.get("text", ""))

                from app.models.atomic_unit import DateRange, Tags

                dates_data = u.get("dates")
                tags_data = u.get("tags")

                tailored_results.append(
                    ScoredUnit(
                        unit_id=unit_id,
                        text=final_text,
                        section=u.get("section", "experience"),
                        org=u.get("org"),
                        role=u.get("role"),
                        dates=DateRange(**dates_data) if dates_data else None,
                        tags=Tags(**tags_data) if tags_data else None,
                        llm_score=float(result.get("score", 5.0)),
                        matched_requirements=[],  # implied in text now
                        reasoning=result.get("changes_made", "Original text preserved"),
                    )
                )

        except Exception as e:
            # On failure, return units with original text and default metadata
            print(f"Tailoring failed: {e}")
            for u in tailorable:
                tailored_results.append(
                    ScoredUnit(
                        unit_id=u.get("id"),
                        text=u.get("text", ""),  # Fallback to original
                        section=u.get("section", "experience"),
                        org=u.get("org"),
                        role=u.get("role"),
                        dates=u.get("dates"),
                        tags=u.get("tags"),
                        llm_score=5.0,
                        matched_requirements=[],
                        reasoning="Tailoring failed - original text preserved",
                    )
                )

    # Append passthrough units (untailored)
    for u in passthrough_units:
        tailored_results.append(
            ScoredUnit(
                unit_id=u.get("id"),
                text=u.get("text", ""),
                section=u.get("section", u.get("section", "skills")),  # Fallback section
                org=u.get("org"),
                role=u.get("role"),
                dates=u.get("dates"),
                tags=u.get("tags"),
                llm_score=10.0,  # Always include
                matched_requirements=[],
                reasoning=f"{u.get('type')} entry preserved",
            )
        )

    return tailored_results
