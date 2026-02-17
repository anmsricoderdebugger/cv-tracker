from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.config import settings
from backend.models.cv_file import CVFile
from backend.models.parsed_cv import ParsedCV
from backend.services.file_parser import extract_text
from backend.utils.llm_client import call_llm, is_llm_available

CV_PARSE_SYSTEM_PROMPT = """You are a professional resume/CV parser. Extract structured information from the given CV text.

Return a JSON object with these fields:
{
  "candidate_name": "Full name of the candidate",
  "email": "email@example.com or null",
  "phone": "phone number or null",
  "total_experience_years": 5.0,
  "skills": ["Python", "SQL", "Machine Learning"],
  "experience": [
    {
      "company": "Company Name",
      "title": "Job Title",
      "duration": "Jan 2020 - Dec 2022",
      "description": "Brief description of role"
    }
  ],
  "education": [
    {
      "institution": "University Name",
      "degree": "Bachelor's/Master's/PhD",
      "field": "Computer Science",
      "year": "2020"
    }
  ],
  "projects": [
    {
      "name": "Project Name",
      "description": "What the project does",
      "technologies": ["Python", "React"]
    }
  ],
  "tools": ["Docker", "Git", "AWS", "Jenkins"],
  "certifications": ["AWS Certified Solutions Architect"],
  "summary": "A 2-3 sentence professional summary of the candidate"
}

Rules:
- For total_experience_years, calculate total professional work experience. If unclear, estimate from dates.
- Normalize skill names (e.g., "Python3" -> "Python", "JS" -> "JavaScript")
- If a field cannot be determined, use null for scalars or [] for lists.
- Extract ALL skills mentioned anywhere in the CV.
- Tools should include specific software, platforms, and technologies distinct from general skills.
"""


MAX_CV_CHARS = 15000  # ~4K tokens


def parse_cv_text(raw_text: str) -> dict:
    if not is_llm_available():
        return {"candidate_name": None, "summary": "LLM not configured - raw text stored only"}
    truncated = raw_text[:MAX_CV_CHARS] if len(raw_text) > MAX_CV_CHARS else raw_text
    return call_llm(
        system_prompt=CV_PARSE_SYSTEM_PROMPT,
        user_prompt=truncated,
        response_json=True,
        model=settings.GROQ_FAST_MODEL,
    )


def process_single_cv(db: Session, cv_file_id: str) -> ParsedCV:
    from uuid import UUID

    cv = db.query(CVFile).filter(CVFile.id == UUID(cv_file_id)).first()
    if not cv:
        raise ValueError(f"CV file not found: {cv_file_id}")

    cv.status = "processing"
    db.commit()

    try:
        raw_text = extract_text(cv.file_path)
        parsed_data = parse_cv_text(raw_text)

        existing = db.query(ParsedCV).filter(ParsedCV.cv_file_id == cv.id).first()
        if existing:
            for key, value in parsed_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.raw_text = raw_text
            existing.parse_model = settings.GROQ_MODEL
            existing.parsed_at = datetime.now(timezone.utc)
            parsed_cv = existing
        else:
            parsed_cv = ParsedCV(
                cv_file_id=cv.id,
                candidate_name=parsed_data.get("candidate_name"),
                email=parsed_data.get("email"),
                phone=parsed_data.get("phone"),
                total_experience_years=parsed_data.get("total_experience_years"),
                skills=parsed_data.get("skills"),
                experience=parsed_data.get("experience"),
                education=parsed_data.get("education"),
                projects=parsed_data.get("projects"),
                tools=parsed_data.get("tools"),
                certifications=parsed_data.get("certifications"),
                summary=parsed_data.get("summary"),
                raw_text=raw_text,
                parse_model=settings.GROQ_MODEL,
                parsed_at=datetime.now(timezone.utc),
            )
            db.add(parsed_cv)

        cv.status = "processed"
        cv.processed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(parsed_cv)
        return parsed_cv

    except Exception as e:
        cv.status = "error"
        cv.error_message = str(e)[:500]
        db.commit()
        raise
