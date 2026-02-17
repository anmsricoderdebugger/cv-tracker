def generate_explanation(match_result: dict, jd: dict, parsed_cv: dict) -> str:
    """Generate human-readable explanation for match result.
    This is used as a fallback when the LLM-generated explanation is insufficient."""
    parts = []
    fit = match_result.get("fit_status", "")

    if fit == "red":
        parts.append("This candidate is a LOW fit for this role.")
    elif fit == "yellow":
        parts.append("This candidate is a MODERATE fit for this role.")
    else:
        parts.append("This candidate is a STRONG fit for this role.")

    # Experience gap
    required_exp = jd.get("min_experience_years")
    candidate_exp = parsed_cv.get("total_experience_years")
    if required_exp and candidate_exp is not None:
        if candidate_exp < required_exp:
            parts.append(
                f"Experience required: {required_exp} years, candidate has {candidate_exp} years."
            )
        else:
            parts.append(
                f"Experience meets requirement: {candidate_exp} years (required: {required_exp})."
            )

    # Missing skills
    missing = match_result.get("missing_skills", [])
    if missing:
        parts.append(f"Missing key skills: {', '.join(missing[:5])}.")

    # Matched skills
    matched = match_result.get("matched_skills", [])
    if matched:
        parts.append(f"Matching skills: {', '.join(matched[:5])}.")

    # Gaps
    gaps = match_result.get("gaps", [])
    for gap in gaps[:3]:
        parts.append(f"- {gap}")

    return "\n".join(parts)
