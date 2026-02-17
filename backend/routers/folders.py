from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from backend.dependencies import get_current_user, get_db
from backend.models.user import User
from backend.schemas.folder import FolderCreate, FolderResponse, FolderStatusResponse, ScanResultResponse
from backend.services.folder_service import (
    add_uploaded_files,
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


@router.post("/{folder_id}/upload")
async def upload_cvs(
    folder_id: UUID,
    files: list[UploadFile] = File(...),
    auto_process: bool = True,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    folder = get_folder(db, folder_id, user.id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    file_data = []
    for f in files:
        content = await f.read()
        file_data.append((f.filename, content))

    result = add_uploaded_files(db, folder, file_data)

    task_id = None
    if auto_process and result["new_cv_ids"]:
        from backend.task_manager import submit_parse_batch

        task_id = submit_parse_batch(result["new_cv_ids"])

    return {**result, "task_id": task_id}


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


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_folder(
    folder_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not delete_folder(db, folder_id, user.id):
        raise HTTPException(status_code=404, detail="Folder not found")
