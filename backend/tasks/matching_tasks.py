import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from uuid import UUID

from backend.database import SessionLocal
from backend.services.matcher import match_cv_to_jd
from backend.tasks.celery_app import celery_app
from backend.utils.redis_client import set_task_progress

logger = logging.getLogger(__name__)

MAX_PARALLEL = 5  # concurrent Groq API calls


def _match_one(cv_file_id: str, jd_id: str) -> dict:
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
        logger.error(f"Failed to match CV {cv_file_id} to JD {jd_id}: {e}")
        return {"cv_file_id": cv_file_id, "status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task(bind=True, name="match_cv")
def match_cv_task(self, cv_file_id: str, jd_id: str):
    return _match_one(cv_file_id, jd_id)


@celery_app.task(bind=True, name="batch_match")
def batch_match_task(self, cv_file_ids: list[str], jd_id: str):
    total = len(cv_file_ids)
    task_id = self.request.id
    set_task_progress(task_id, 0, total, "matching", f"Matching {total} CVs")

    results = []
    done_count = 0

    with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
        futures = {pool.submit(_match_one, cv_id, jd_id): cv_id for cv_id in cv_file_ids}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            done_count += 1
            set_task_progress(task_id, done_count, total, "matching", f"Matched {done_count}/{total}")

    set_task_progress(task_id, total, total, "completed", "All CVs matched")
    return {"total": total, "results": results}
