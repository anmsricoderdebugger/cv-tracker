import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from backend.database import Base


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    required_skills: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    preferred_skills: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    min_experience_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    education_requirements: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    key_responsibilities: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    keywords: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    scoring_weights: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="job_descriptions")
    match_results = relationship("MatchResult", back_populates="job_description")
