import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from backend.config import settings
from backend.models.cv_file import CVFile
from backend.models.monitored_folder import MonitoredFolder
from backend.utils.hashing import compute_file_hash, compute_hash_from_bytes


UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "cv_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def register_folder(
    db: Session, user_id: UUID, folder_path: str | None = None, label: str | None = None
) -> MonitoredFolder:
    label = label or folder_path or "Uploaded CVs"
    # Use a virtual path for cloud deployment
    virtual_path = folder_path if folder_path else f"cloud://{label}"

    existing = (
        db.query(MonitoredFolder)
        .filter(MonitoredFolder.user_id == user_id, MonitoredFolder.folder_path == virtual_path)
        .first()
    )
    if existing:
        raise ValueError("Collection already exists with this name")

    folder = MonitoredFolder(
        user_id=user_id,
        folder_path=virtual_path,
        label=label,
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


def add_uploaded_files(
    db: Session, folder: MonitoredFolder, files: list[tuple[str, bytes]]
) -> dict:
    """Add uploaded CV files to a folder collection.

    Args:
        files: list of (filename, file_bytes) tuples
    """
    allowed_exts = set(settings.ALLOWED_EXTENSIONS)
    new_count = 0
    skipped_count = 0
    new_cv_ids = []

    for filename, content in files:
        ext = Path(filename).suffix.lower()
        if ext not in allowed_exts:
            continue

        file_hash = compute_hash_from_bytes(content)

        # Check for duplicate by hash within this folder
        existing = (
            db.query(CVFile)
            .filter(CVFile.folder_id == folder.id, CVFile.file_hash == file_hash)
            .first()
        )
        if existing:
            skipped_count += 1
            continue

        # Save file to temp upload dir for processing
        upload_path = os.path.join(UPLOAD_DIR, f"{file_hash}{ext}")
        with open(upload_path, "wb") as f:
            f.write(content)

        cv = CVFile(
            folder_id=folder.id,
            file_name=filename,
            file_path=upload_path,
            file_hash=file_hash,
            file_size_bytes=len(content),
            status="new",
        )
        db.add(cv)
        db.flush()
        new_count += 1
        new_cv_ids.append(cv.id)

    folder.last_scanned_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "total_uploaded": len(files),
        "new": new_count,
        "skipped": skipped_count,
        "new_cv_ids": [str(cid) for cid in new_cv_ids],
    }


def scan_folder(db: Session, folder: MonitoredFolder) -> dict:
    """Scan a local folder for CV files. Only works for local folder paths."""
    folder_path = folder.folder_path

    # Cloud/virtual folders can't be scanned
    if folder_path.startswith("cloud://"):
        return {
            "total_on_disk": 0,
            "new": 0,
            "modified": 0,
            "skipped": 0,
            "new_cv_ids": [],
        }

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
