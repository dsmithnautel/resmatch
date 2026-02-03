"""LLM-based tailoring service for atomic units against job descriptions."""

import json
from typing import Any

from app.models import ParsedJD, ScoredUnit
from app.services.gemini import generate_json

TAILORING_PROMPT = """
You are a professional resume writer. Your goal is to tailor the applicant's resume bullet points to better match the provided Job Description (JD), while strictly preserving the truth and original meaning.

For EACH bullet point provided:
1. Analyze its content and the JD requirements.
2. REWRITE the bullet point to highlight relevance to the JD keywords and responsibilities.
   - Use active voice and strong action verbs.
   - Incorporate JD keywords naturally where honest and applicable.
   - Improve clarity and impact.
   - DO NOT fabricate experiences or change the core meaning.
   - Keep the length similar to the original.
3. Assign a relevance score (0-10) based on how well the *original* content matches the JD.

JOB DESCRIPTION:
Company: {company}
Role: {role_title}

Must-Have Requirements:
{must_haves}

Key Responsibilities:
{responsibilities}

Technical Keywords: {keywords}

---

RESUME BULLETS TO TAILOR:
{bullets_json}

---

Return a JSON array with one object per bullet:
[
  {{
    "id": "bullet_id",
    "original_text": "...", 
    "tailored_text": "The reworded version of the bullet...",
    "score": 8.5,
    "changes_made": "Brief explanation of how it was reworded..."
  }},
  ...
]
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
