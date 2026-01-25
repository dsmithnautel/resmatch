"""Greedy optimizer for selecting resume bullets under constraints."""

from collections import defaultdict

from app.models import CompileConstraints, CoverageStats, ParsedJD, ScoredUnit


def optimize_selection(
    scored_units: list[ScoredUnit], parsed_jd: ParsedJD, constraints: CompileConstraints
) -> tuple[list[ScoredUnit], CoverageStats]:
    """
    Select optimal set of bullets under constraints.

    Greedy algorithm:
    1. Sort by LLM score (already done)
    2. Select greedily while respecting:
       - Section quotas (max experience bullets, max project bullets)
       - Diversity (max bullets per role)
       - Character budget (one-page limit)
    3. Track coverage of must-haves
    4. Prioritize uncovered requirements
    """
    selected: list[ScoredUnit] = []
    total_chars = 0

    # Track counts by section and by role
    section_counts: dict[str, int] = defaultdict(int)
    role_counts: dict[str, int] = defaultdict(int)

    # Track which must-haves are covered
    covered_requirements = set()

    # Section limits
    section_limits = {
        "experience": constraints.max_experience_bullets,
        "projects": constraints.max_project_bullets,
        "education": 3,  # Usually 1-3 education entries
    }

    for unit in scored_units:
        # Check section quota
        section_limit = section_limits.get(unit.section, 10)
        if section_counts[unit.section] >= section_limit:
            continue

        # Check diversity (max bullets per role)
        role_key = f"{unit.org}_{unit.role}"
        if role_counts[role_key] >= constraints.max_bullets_per_role:
            continue

        # Check character budget
        if total_chars + len(unit.text) > constraints.max_total_chars:
            continue

        # Check minimum score threshold (skip very low scores)
        if unit.llm_score < 3.0:
            continue

        # Select this unit
        unit.selected = True
        selected.append(unit)

        # Update tracking
        section_counts[unit.section] += 1
        role_counts[role_key] += 1
        total_chars += len(unit.text)

        # Track covered requirements
        for req in unit.matched_requirements:
            covered_requirements.add(req.lower())

    # Calculate coverage
    must_haves_lower = {mh.lower() for mh in parsed_jd.must_haves}
    matched_count = 0
    for mh in must_haves_lower:
        # Check if any covered requirement mentions this must-have
        for covered in covered_requirements:
            if mh in covered or covered in mh:
                matched_count += 1
                break

    coverage = CoverageStats(
        must_haves_matched=matched_count,
        must_haves_total=len(parsed_jd.must_haves),
        coverage_score=matched_count / max(len(parsed_jd.must_haves), 1),
    )

    return selected, coverage
