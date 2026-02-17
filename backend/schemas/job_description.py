from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


class JDCreateText(BaseModel):
    title: str
    raw_text: str
    scoring_weights: dict | None = None

    @field_validator("scoring_weights")
    @classmethod
    def validate_weights(cls, v):
        if v is not None:
            total = sum(v.values())
            if abs(total - 1.0) > 0.01:
                raise ValueError(f"Weights must sum to 1.0, got {total}")
        return v


class JDUpdateWeights(BaseModel):
    skills: float
    experience: float
    projects: float
    keywords: float

    @field_validator("keywords")
    @classmethod
    def validate_total(cls, v, info):
        total = (
            info.data.get("skills", 0)
            + info.data.get("experience", 0)
            + info.data.get("projects", 0)
            + v
        )
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        return v


class JDResponse(BaseModel):
    id: UUID
    title: str
    raw_text: str
    required_skills: list | None = None
    preferred_skills: list | None = None
    min_experience_years: int | None = None
    education_requirements: list | None = None
    key_responsibilities: list | None = None
    keywords: list | None = None
    scoring_weights: dict | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
