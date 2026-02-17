from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ParsedCVResponse(BaseModel):
    id: UUID
    cv_file_id: UUID
    candidate_name: str | None
    email: str | None
    phone: str | None
    total_experience_years: float | None
    skills: list | None
    experience: list | None
    education: list | None
    projects: list | None
    tools: list | None
    certifications: list | None
    summary: str | None
    parse_model: str | None
    parsed_at: datetime | None

    model_config = {"from_attributes": True}


class CVDetailResponse(BaseModel):
    id: UUID
    file_name: str
    file_path: str
    file_hash: str
    file_size_bytes: int | None
    status: str
    error_message: str | None
    detected_at: datetime
    processed_at: datetime | None
    parsed_cv: ParsedCVResponse | None = None

    model_config = {"from_attributes": True}
