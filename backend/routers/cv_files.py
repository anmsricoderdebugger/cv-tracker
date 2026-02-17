from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from backend.dependencies import get_current_user, get_db
from backend.models.cv_file import CVFile
from backend.models.monitored_folder import MonitoredFolder
from backend.models.user import User
from backend.schemas.cv_file import CVFileResponse
from backend.schemas.parsed_cv import CVDetailResponse

router = APIRouter(prefix="/api/v1/cvs", tags=["cv_files"])


@router.get("/", response_model=list[CVFileResponse])
def list_cvs(
    folder_id: UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = (
        db.query(CVFile)
        .join(MonitoredFolder)
        .filter(MonitoredFolder.user_id == user.id)
    )
    if folder_id:
        query = query.filter(CVFile.folder_id == folder_id)
    if status_filter:
        query = query.filter(CVFile.status == status_filter)
    return query.order_by(CVFile.created_at.desc()).all()


@router.get("/progress/{task_id}")
def check_progress(task_id: str):
    from backend.task_manager import get_progress

    progress = get_progress(task_id)
    if not progress:
        return {"current": 0, "total": 0, "status": "unknown", "message": "Task not found"}
    return progress


@router.get("/{cv_id}", response_model=CVDetailResponse)
def get_cv_detail(
    cv_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cv = (
        db.query(CVFile)
        .options(joinedload(CVFile.parsed_cv))
        .join(MonitoredFolder)
        .filter(CVFile.id == cv_id, MonitoredFolder.user_id == user.id)
        .first()
    )
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    return cv
