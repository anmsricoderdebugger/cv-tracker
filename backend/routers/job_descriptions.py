from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.dependencies import get_current_user, get_db
from backend.models.user import User
from backend.schemas.job_description import JDCreateText, JDResponse, JDUpdateWeights
from backend.services.jd_service import (
    create_jd_from_file,
    create_jd_from_text,
    delete_jd,
    get_jd,
    get_user_jds,
    update_jd_weights,
)

router = APIRouter(prefix="/api/v1/jds", tags=["job_descriptions"])


@router.post("/", response_model=JDResponse, status_code=status.HTTP_201_CREATED)
def create_jd_text(
    body: JDCreateText,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    jd = create_jd_from_text(db, user.id, body.title, body.raw_text, body.scoring_weights)
    return jd


@router.post("/upload", response_model=JDResponse, status_code=status.HTTP_201_CREATED)
async def create_jd_file(
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    content = await file.read()
    jd = create_jd_from_file(db, user.id, title, content, file.filename)
    return jd


@router.get("/", response_model=list[JDResponse])
def list_jds(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_user_jds(db, user.id)


@router.get("/{jd_id}", response_model=JDResponse)
def get_jd_detail(
    jd_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    jd = get_jd(db, jd_id, user.id)
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")
    return jd


@router.put("/{jd_id}/weights", response_model=JDResponse)
def update_weights(
    jd_id: UUID,
    body: JDUpdateWeights,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    weights = {
        "skills": body.skills,
        "experience": body.experience,
        "projects": body.projects,
        "keywords": body.keywords,
    }
    try:
        jd = update_jd_weights(db, jd_id, user.id, weights)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")
    return jd


@router.delete("/{jd_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_jd(
    jd_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    if not delete_jd(db, jd_id, user.id):
        raise HTTPException(status_code=404, detail="Job description not found")
