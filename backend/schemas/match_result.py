from uuid import UUID

from pydantic import BaseModel


class MatchRequest(BaseModel):
    jd_id: UUID
    cv_file_ids: list[UUID] | None = None
    weights: dict | None = None


class MatchResponse(BaseModel):
    task_id: str
    total_cvs: int


class LeaderboardEntry(BaseModel):
    rank: int
    match_id: str
    cv_file_id: str
    candidate_name: str
    overall_score: float
    skills_score: float
    experience_score: float
    projects_score: float
    keywords_score: float
    fit_status: str
    matched_skills: list
    missing_skills: list
    strengths: list
    gaps: list
    explanation: str | None
