from uuid import UUID

from sqlalchemy.orm import Session

from backend.models.job_description import JobDescription
from backend.services.file_parser import extract_text_from_bytes
from backend.utils.llm_client import call_llm, is_llm_available

JD_PARSE_SYSTEM_PROMPT = """You are a job description parser. Extract structured information from the given job description text.

Return a JSON object with these fields:
{
  "title": "Job title extracted or inferred from the JD",
  "required_skills": ["list", "of", "required", "skills"],
  "preferred_skills": ["list", "of", "preferred/nice-to-have", "skills"],
  "min_experience_years": 3,
  "education_requirements": ["Bachelor's in CS or related field"],
  "key_responsibilities": ["responsibility 1", "responsibility 2"],
  "keywords": ["key", "technical", "terms", "tools", "technologies"]
}

If a field cannot be determined, use null for scalars or [] for lists.
For min_experience_years, extract the minimum years mentioned. If a range is given (e.g., "3-5 years"), use the lower bound.
"""


def parse_jd_with_llm(raw_text: str) -> dict:
    if not is_llm_available():
        return {}
    return call_llm(
        system_prompt=JD_PARSE_SYSTEM_PROMPT,
        user_prompt=raw_text,
        response_json=True,
    )


def create_jd_from_text(
    db: Session, user_id: UUID, title: str, raw_text: str, scoring_weights: dict | None = None
) -> JobDescription:
    parsed = parse_jd_with_llm(raw_text)

    jd = JobDescription(
        user_id=user_id,
        title=title or parsed.get("title", "Untitled"),
        raw_text=raw_text,
        required_skills=parsed.get("required_skills"),
        preferred_skills=parsed.get("preferred_skills"),
        min_experience_years=parsed.get("min_experience_years"),
        education_requirements=parsed.get("education_requirements"),
        key_responsibilities=parsed.get("key_responsibilities"),
        keywords=parsed.get("keywords"),
        scoring_weights=scoring_weights,
    )
    db.add(jd)
    db.commit()
    db.refresh(jd)
    return jd


def create_jd_from_file(
    db: Session,
    user_id: UUID,
    title: str,
    file_content: bytes,
    filename: str,
    scoring_weights: dict | None = None,
) -> JobDescription:
    raw_text = extract_text_from_bytes(file_content, filename)
    return create_jd_from_text(db, user_id, title, raw_text, scoring_weights)


def get_user_jds(db: Session, user_id: UUID) -> list[JobDescription]:
    return (
        db.query(JobDescription)
        .filter(JobDescription.user_id == user_id, JobDescription.is_active.is_(True))
        .order_by(JobDescription.created_at.desc())
        .all()
    )


def get_jd(db: Session, jd_id: UUID, user_id: UUID) -> JobDescription | None:
    return (
        db.query(JobDescription)
        .filter(JobDescription.id == jd_id, JobDescription.user_id == user_id)
        .first()
    )


def update_jd_weights(
    db: Session, jd_id: UUID, user_id: UUID, weights: dict
) -> JobDescription | None:
    jd = get_jd(db, jd_id, user_id)
    if not jd:
        return None
    total = sum(weights.values())
    if abs(total - 1.0) > 0.01:
        raise ValueError(f"Weights must sum to 1.0, got {total}")
    jd.scoring_weights = weights
    db.commit()
    db.refresh(jd)
    return jd


def delete_jd(db: Session, jd_id: UUID, user_id: UUID) -> bool:
    jd = get_jd(db, jd_id, user_id)
    if not jd:
        return False
    jd.is_active = False
    db.commit()
    return True
