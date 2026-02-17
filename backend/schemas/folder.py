from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class FolderCreate(BaseModel):
    folder_path: str | None = None
    label: str | None = None


class FolderResponse(BaseModel):
    id: UUID
    folder_path: str
    label: str | None
    is_watching: bool
    last_scanned_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class FolderStatusResponse(BaseModel):
    folder_id: str
    folder_path: str
    label: str | None
    is_watching: bool
    last_scanned_at: str | None
    total_cvs: int
    status_counts: dict


class ScanResultResponse(BaseModel):
    total_on_disk: int
    new: int
    modified: int
    skipped: int
    new_cv_ids: list[str]
