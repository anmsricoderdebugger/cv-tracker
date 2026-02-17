"""In-process background task manager replacing Celery + Redis.

Stores task progress in memory. Suitable for single-process deployments
(Render free tier, small VPS). For production scale, swap back to Celery.
"""

import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

MAX_PARALLEL = 5


@dataclass
class TaskProgress:
    current: int = 0
    total: int = 0
    status: str = "pending"
    message: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


_tasks: dict[str, TaskProgress] = {}
_lock = threading.Lock()
_pool = ThreadPoolExecutor(max_workers=4)


def get_progress(task_id: str) -> dict | None:
    with _lock:
        t = _tasks.get(task_id)
        if not t:
            return None
        return {
            "current": t.current,
            "total": t.total,
            "status": t.status,
            "message": t.message,
        }


def _set_progress(task_id: str, current: int, total: int, status: str, message: str):
    with _lock:
        if task_id not in _tasks:
            _tasks[task_id] = TaskProgress()
        t = _tasks[task_id]
        t.current = current
        t.total = total
        t.status = status
        t.message = message


def _parse_one(cv_file_id: str) -> dict:
    from backend.database import SessionLocal
    from backend.services.cv_parser import process_single_cv

    db = SessionLocal()
    try:
        parsed_cv = process_single_cv(db, cv_file_id)
        return {"cv_file_id": cv_file_id, "status": "success", "name": parsed_cv.candidate_name}
    except Exception as e:
        logger.error(f"Failed to parse CV {cv_file_id}: {e}")
        return {"cv_file_id": cv_file_id, "status": "error", "error": str(e)}
    finally:
        db.close()


def _match_one(cv_file_id: str, jd_id: str) -> dict:
    from uuid import UUID

    from backend.database import SessionLocal
    from backend.services.matcher import match_cv_to_jd

    db = SessionLocal()
    try:
        result = match_cv_to_jd(db, UUID(cv_file_id), UUID(jd_id))
        return {
            "cv_file_id": cv_file_id,
            "status": "success",
            "score": result.overall_score,
            "fit_status": result.fit_status,
        }
    except Exception as e:
        logger.error(f"Failed to match CV {cv_file_id}: {e}")
        return {"cv_file_id": cv_file_id, "status": "error", "error": str(e)}
    finally:
        db.close()


def _run_parse_batch(task_id: str, cv_file_ids: list[str]):
    total = len(cv_file_ids)
    _set_progress(task_id, 0, total, "processing", f"Processing {total} CVs")

    done_count = 0
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
        futures = {pool.submit(_parse_one, cv_id): cv_id for cv_id in cv_file_ids}
        for future in as_completed(futures):
            future.result()
            done_count += 1
            _set_progress(task_id, done_count, total, "processing", f"Processed {done_count}/{total}")

    _set_progress(task_id, total, total, "completed", "All CVs processed")


def _run_match_batch(task_id: str, cv_file_ids: list[str], jd_id: str):
    total = len(cv_file_ids)
    _set_progress(task_id, 0, total, "matching", f"Matching {total} CVs")

    done_count = 0
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
        futures = {pool.submit(_match_one, cv_id, jd_id): cv_id for cv_id in cv_file_ids}
        for future in as_completed(futures):
            future.result()
            done_count += 1
            _set_progress(task_id, done_count, total, "matching", f"Matched {done_count}/{total}")

    _set_progress(task_id, total, total, "completed", "All CVs matched")


def submit_parse_batch(cv_file_ids: list[str]) -> str:
    task_id = str(uuid.uuid4())
    _tasks[task_id] = TaskProgress(total=len(cv_file_ids))
    _pool.submit(_run_parse_batch, task_id, cv_file_ids)
    return task_id


def submit_match_batch(cv_file_ids: list[str], jd_id: str) -> str:
    task_id = str(uuid.uuid4())
    _tasks[task_id] = TaskProgress(total=len(cv_file_ids))
    _pool.submit(_run_match_batch, task_id, cv_file_ids, jd_id)
    return task_id
