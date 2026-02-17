import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from backend.database import Base


class MatchResult(Base):
    __tablename__ = "match_results"
    __table_args__ = (UniqueConstraint("cv_file_id", "jd_id", name="uq_cv_jd_match"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cv_file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cv_files.id"), nullable=False, index=True
    )
    jd_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_descriptions.id"), nullable=False, index=True
    )
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    skills_score: Mapped[float] = mapped_column(Float, nullable=False)
    experience_score: Mapped[float] = mapped_column(Float, nullable=False)
    projects_score: Mapped[float] = mapped_column(Float, nullable=False)
    keywords_score: Mapped[float] = mapped_column(Float, nullable=False)
    fit_status: Mapped[str] = mapped_column(String(10), nullable=False)
    matched_skills: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    missing_skills: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    strengths: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    gaps: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    weights_used: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    match_model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    cv_file = relationship("CVFile", back_populates="match_results")
    job_description = relationship("JobDescription", back_populates="match_results")
