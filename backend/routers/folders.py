from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.dependencies import get_current_user, get_db
from backend.models.user import User
from backend.schemas.folder import FolderCreate, FolderResponse, FolderStatusResponse, ScanResultResponse
from backend.services.folder_service import (
    delete_folder,
    get_folder,
    get_folder_status,
    get_user_folders,
    register_folder,
    scan_folder,
)

router = APIRouter(prefix="/api/v1/folders", tags=["folders"])


@router.post("/", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
def create_folder(
    body: FolderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        folder = register_folder(db, user.id, body.folder_path, body.label)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return folder


@router.get("/", response_model=list[FolderResponse])
def list_folders(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_user_folders(db, user.id)


@router.post("/{folder_id}/scan")
def trigger_scan(
    folder_id: UUID,
    auto_process: bool = True,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    folder = get_folder(db, folder_id, user.id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    try:
        result = scan_folder(db, folder)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    task_id = None
    if auto_process and result["new_cv_ids"]:
        from backend.task_manager import submit_parse_batch

        task_id = submit_parse_batch(result["new_cv_ids"])

    return {**result, "task_id": task_id}


@router.get("/{folder_id}/status", response_model=FolderStatusResponse)
def folder_status(
    folder_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    folder = get_folder(db, folder_id, user.id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    return get_folder_status(db, folder)


@router.post("/{folder_id}/watch/start")
def start_watch(
    folder_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    folder = get_folder(db, folder_id, user.id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    from backend.watchers.watcher_manager import start_watching

    started = start_watching(str(folder.id), folder.folder_path)
    if started:
        folder.is_watching = True
        db.commit()
    return {"watching": True, "folder_id": str(folder.id)}


@router.post("/{folder_id}/watch/stop")
def stop_watch(
    folder_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    folder = get_folder(db, folder_id, user.id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    from backend.watchers.watcher_manager import stop_watching

    stop_watching(str(folder.id))
    folder.is_watching = False
    db.commit()
    return {"watching": False, "folder_id": str(folder.id)}


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_folder(
    folder_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from backend.watchers.watcher_manager import stop_watching

    stop_watching(str(folder_id))
    if not delete_folder(db, folder_id, user.id):
        raise HTTPException(status_code=404, detail="Folder not found")
