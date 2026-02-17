from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.dependencies import get_current_user, get_db
from backend.models.cv_file import CVFile
from backend.models.monitored_folder import MonitoredFolder
from backend.models.user import User
from backend.schemas.match_result import LeaderboardEntry, MatchRequest, MatchResponse
from backend.services.matcher import get_leaderboard

router = APIRouter(prefix="/api/v1/matching", tags=["matching"])


@router.post("/", response_model=MatchResponse)
def trigger_matching(
    body: MatchRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if body.cv_file_ids:
        cv_ids = [str(cid) for cid in body.cv_file_ids]
    else:
        cvs = (
            db.query(CVFile)
            .join(MonitoredFolder)
            .filter(
                MonitoredFolder.user_id == user.id,
                CVFile.status == "processed",
            )
            .all()
        )
        cv_ids = [str(cv.id) for cv in cvs]

    if not cv_ids:
        raise HTTPException(status_code=400, detail="No processed CVs available for matching")

    from backend.task_manager import submit_match_batch

    task_id = submit_match_batch(cv_ids, str(body.jd_id))
    return MatchResponse(task_id=task_id, total_cvs=len(cv_ids))


@router.get("/leaderboard/{jd_id}", response_model=list[LeaderboardEntry])
def leaderboard(
    jd_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_leaderboard(db, jd_id)
