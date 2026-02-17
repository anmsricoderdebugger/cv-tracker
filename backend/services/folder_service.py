import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from backend.config import settings
from backend.models.cv_file import CVFile
from backend.models.monitored_folder import MonitoredFolder
from backend.utils.hashing import compute_file_hash


def register_folder(
    db: Session, user_id: UUID, folder_path: str, label: str | None = None
) -> MonitoredFolder:
    folder_path = str(Path(folder_path).resolve())
    if not os.path.isdir(folder_path):
        raise ValueError(f"Folder does not exist: {folder_path}")

    existing = (
        db.query(MonitoredFolder)
        .filter(MonitoredFolder.user_id == user_id, MonitoredFolder.folder_path == folder_path)
        .first()
    )
    if existing:
        raise ValueError("Folder already registered")

    folder = MonitoredFolder(
        user_id=user_id,
        folder_path=folder_path,
        label=label or Path(folder_path).name,
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


def scan_folder(db: Session, folder: MonitoredFolder) -> dict:
    folder_path = folder.folder_path
    if not os.path.isdir(folder_path):
        raise ValueError(f"Folder no longer exists: {folder_path}")

    allowed_exts = set(settings.ALLOWED_EXTENSIONS)
    disk_files = {}
    for entry in os.scandir(folder_path):
        if entry.is_file():
            ext = Path(entry.name).suffix.lower()
            if ext in allowed_exts:
                disk_files[entry.path] = entry

    existing_cvs = {
        cv.file_path: cv
        for cv in db.query(CVFile).filter(CVFile.folder_id == folder.id).all()
    }

    new_count = 0
    modified_count = 0
    skipped_count = 0
    new_cv_ids = []

    for file_path, entry in disk_files.items():
        file_hash = compute_file_hash(file_path)
        file_size = entry.stat().st_size

        if file_path in existing_cvs:
            cv = existing_cvs[file_path]
            if cv.file_hash == file_hash:
                skipped_count += 1
            else:
                cv.file_hash = file_hash
                cv.file_size_bytes = file_size
                cv.status = "modified"
                cv.error_message = None
                modified_count += 1
                new_cv_ids.append(cv.id)
        else:
            cv = CVFile(
                folder_id=folder.id,
                file_name=Path(file_path).name,
                file_path=file_path,
                file_hash=file_hash,
                file_size_bytes=file_size,
                status="new",
            )
            db.add(cv)
            db.flush()
            new_count += 1
            new_cv_ids.append(cv.id)

    folder.last_scanned_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "total_on_disk": len(disk_files),
        "new": new_count,
        "modified": modified_count,
        "skipped": skipped_count,
        "new_cv_ids": [str(cid) for cid in new_cv_ids],
    }


def get_folder_status(db: Session, folder: MonitoredFolder) -> dict:
    cvs = db.query(CVFile).filter(CVFile.folder_id == folder.id).all()
    status_counts = {}
    for cv in cvs:
        status_counts[cv.status] = status_counts.get(cv.status, 0) + 1

    return {
        "folder_id": str(folder.id),
        "folder_path": folder.folder_path,
        "label": folder.label,
        "is_watching": folder.is_watching,
        "last_scanned_at": folder.last_scanned_at.isoformat() if folder.last_scanned_at else None,
        "total_cvs": len(cvs),
        "status_counts": status_counts,
    }


def get_user_folders(db: Session, user_id: UUID) -> list[MonitoredFolder]:
    return (
        db.query(MonitoredFolder)
        .filter(MonitoredFolder.user_id == user_id)
        .order_by(MonitoredFolder.created_at.desc())
        .all()
    )


def get_folder(db: Session, folder_id: UUID, user_id: UUID) -> MonitoredFolder | None:
    return (
        db.query(MonitoredFolder)
        .filter(MonitoredFolder.id == folder_id, MonitoredFolder.user_id == user_id)
        .first()
    )


def delete_folder(db: Session, folder_id: UUID, user_id: UUID) -> bool:
    folder = get_folder(db, folder_id, user_id)
    if not folder:
        return False
    db.delete(folder)
    db.commit()
    return True
