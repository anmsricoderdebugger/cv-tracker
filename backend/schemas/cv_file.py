from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CVFileResponse(BaseModel):
    id: UUID
    folder_id: UUID
    file_name: str
    file_path: str
    file_hash: str
    file_size_bytes: int | None
    status: str
    error_message: str | None
    detected_at: datetime
    processed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
