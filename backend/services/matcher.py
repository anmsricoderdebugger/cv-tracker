from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from backend.config import settings
from backend.models.cv_file import CVFile
from backend.models.job_description import JobDescription
from backend.models.match_result import MatchResult
from backend.models.parsed_cv import ParsedCV
from backend.utils.llm_client import call_llm, is_llm_available

MATCH_SYSTEM_PROMPT = """You are an ATS (Applicant Tracking System) matching engine. Compare a candidate's CV against a Job Description and evaluate fit.

You will receive a JSON with two keys: "job_description" and "candidate_cv".

Return a JSON object with these fields:
{
  "skills_score": 75,
  "experience_score": 60,
  "projects_score": 50,
  "keywords_score": 80,
  "matched_skills": ["Python", "SQL", "Docker"],
  "missing_skills": ["Kubernetes", "Terraform"],
  "strengths": [
    "Strong Python experience with 5+ years",
    "Relevant ML project experience"
  ],
  "gaps": [
    "Missing required DevOps skills (Kubernetes, Terraform)",
    "Only 2 years experience vs 5 years required"
  ],
  "explanation": "The candidate has strong programming skills but lacks the required DevOps and infrastructure experience. Their ML project background is relevant but they need more years of professional experience."
}

Scoring guidelines (each score is 0-100):
- skills_score: % of required skills the candidate has. Include partial matches for related skills.
- experience_score: How well the candidate's years and type of experience match. 100 if meets/exceeds requirements.
- projects_score: How relevant the candidate's projects are to the role's responsibilities.
- keywords_score: Overlap of technical tools, technologies, and domain keywords.

Be fair and objective. Provide actionable, specific feedback in strengths and gaps.
"""


def get_weights(jd: JobDescription) -> dict:
    if jd.scoring_weights:
        return jd.scoring_weights
    return {
        "skills": settings.DEFAULT_SKILL_WEIGHT,
        "experience": settings.DEFAULT_EXPERIENCE_WEIGHT,
        "projects": settings.DEFAULT_PROJECT_WEIGHT,
        "keywords": settings.DEFAULT_KEYWORD_WEIGHT,
    }


def compute_fit_status(score: float) -> str:
    if score >= 70:
        return "green"
    elif score >= 45:
        return "yellow"
    return "red"


def match_cv_to_jd(db: Session, cv_file_id: UUID, jd_id: UUID) -> MatchResult:
    cv = db.query(CVFile).filter(CVFile.id == cv_file_id).first()
    if not cv:
        raise ValueError(f"CV file not found: {cv_file_id}")

    parsed_cv = db.query(ParsedCV).filter(ParsedCV.cv_file_id == cv_file_id).first()
    if not parsed_cv:
        raise ValueError(f"CV not parsed yet: {cv_file_id}")

    jd = db.query(JobDescription).filter(JobDescription.id == jd_id).first()
    if not jd:
        raise ValueError(f"Job description not found: {jd_id}")

    jd_data = {
        "title": jd.title,
        "required_skills": jd.required_skills or [],
        "preferred_skills": jd.preferred_skills or [],
        "min_experience_years": jd.min_experience_years,
        "education_requirements": jd.education_requirements or [],
        "key_responsibilities": jd.key_responsibilities or [],
        "keywords": jd.keywords or [],
    }
    cv_data = {
        "candidate_name": parsed_cv.candidate_name,
        "total_experience_years": parsed_cv.total_experience_years,
        "skills": parsed_cv.skills or [],
        "experience": parsed_cv.experience or [],
        "education": parsed_cv.education or [],
        "projects": parsed_cv.projects or [],
        "tools": parsed_cv.tools or [],
        "certifications": parsed_cv.certifications or [],
        "summary": parsed_cv.summary,
    }

    import json

    if not is_llm_available():
        result = {
            "skills_score": 0,
            "experience_score": 0,
            "projects_score": 0,
            "keywords_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "strengths": [],
            "gaps": ["Vertex AI not configured - unable to perform AI matching"],
            "explanation": "Vertex AI not configured. Set VERTEX_PROJECT_ID in .env to enable AI matching.",
        }
    else:
        match_input = json.dumps({"job_description": jd_data, "candidate_cv": cv_data})
        result = call_llm(
            system_prompt=MATCH_SYSTEM_PROMPT,
            user_prompt=match_input,
            response_json=True,
        )

    weights = get_weights(jd)
    overall_score = (
        result.get("skills_score", 0) * weights.get("skills", 0.4)
        + result.get("experience_score", 0) * weights.get("experience", 0.3)
        + result.get("projects_score", 0) * weights.get("projects", 0.2)
        + result.get("keywords_score", 0) * weights.get("keywords", 0.1)
    )
    overall_score = round(overall_score, 2)
    fit_status = compute_fit_status(overall_score)

    existing = (
        db.query(MatchResult)
        .filter(MatchResult.cv_file_id == cv_file_id, MatchResult.jd_id == jd_id)
        .first()
    )

    if existing:
        existing.overall_score = overall_score
        existing.skills_score = result.get("skills_score", 0)
        existing.experience_score = result.get("experience_score", 0)
        existing.projects_score = result.get("projects_score", 0)
        existing.keywords_score = result.get("keywords_score", 0)
        existing.fit_status = fit_status
        existing.matched_skills = result.get("matched_skills")
        existing.missing_skills = result.get("missing_skills")
        existing.strengths = result.get("strengths")
        existing.gaps = result.get("gaps")
        existing.explanation = result.get("explanation")
        existing.weights_used = weights
        existing.match_model = settings.VERTEX_MODEL
        match_result = existing
    else:
        match_result = MatchResult(
            cv_file_id=cv_file_id,
            jd_id=jd_id,
            overall_score=overall_score,
            skills_score=result.get("skills_score", 0),
            experience_score=result.get("experience_score", 0),
            projects_score=result.get("projects_score", 0),
            keywords_score=result.get("keywords_score", 0),
            fit_status=fit_status,
            matched_skills=result.get("matched_skills"),
            missing_skills=result.get("missing_skills"),
            strengths=result.get("strengths"),
            gaps=result.get("gaps"),
            explanation=result.get("explanation"),
            weights_used=weights,
            match_model=settings.VERTEX_MODEL,
        )
        db.add(match_result)

    db.commit()
    db.refresh(match_result)
    return match_result


def get_leaderboard(db: Session, jd_id: UUID) -> list[dict]:
    results = (
        db.query(MatchResult, ParsedCV)
        .join(ParsedCV, MatchResult.cv_file_id == ParsedCV.cv_file_id)
        .filter(MatchResult.jd_id == jd_id)
        .order_by(MatchResult.overall_score.desc())
        .all()
    )

    leaderboard = []
    for rank, (match, parsed) in enumerate(results, 1):
        leaderboard.append({
            "rank": rank,
            "match_id": str(match.id),
            "cv_file_id": str(match.cv_file_id),
            "candidate_name": parsed.candidate_name or "Unknown",
            "overall_score": match.overall_score,
            "skills_score": match.skills_score,
            "experience_score": match.experience_score,
            "projects_score": match.projects_score,
            "keywords_score": match.keywords_score,
            "fit_status": match.fit_status,
            "matched_skills": match.matched_skills or [],
            "missing_skills": match.missing_skills or [],
            "strengths": match.strengths or [],
            "gaps": match.gaps or [],
            "explanation": match.explanation,
        })
    return leaderboard
