import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from backend.database import SessionLocal
from backend.services.cv_parser import process_single_cv
from backend.tasks.celery_app import celery_app
from backend.utils.redis_client import set_task_progress

logger = logging.getLogger(__name__)

MAX_PARALLEL = 5  # concurrent Groq API calls


def _parse_one(cv_file_id: str) -> dict:
    db = SessionLocal()
    try:
        parsed_cv = process_single_cv(db, cv_file_id)
        return {"cv_file_id": cv_file_id, "status": "success", "name": parsed_cv.candidate_name}
    except Exception as e:
        logger.error(f"Failed to parse CV {cv_file_id}: {e}")
        return {"cv_file_id": cv_file_id, "status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task(bind=True, name="parse_cv")
def parse_cv_task(self, cv_file_id: str):
    return _parse_one(cv_file_id)


@celery_app.task(bind=True, name="process_folder")
def process_folder_task(self, cv_file_ids: list[str]):
    total = len(cv_file_ids)
    task_id = self.request.id
    set_task_progress(task_id, 0, total, "processing", f"Processing {total} CVs")

    results = []
    done_count = 0

    with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
        futures = {pool.submit(_parse_one, cv_id): cv_id for cv_id in cv_file_ids}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            done_count += 1
            set_task_progress(task_id, done_count, total, "processing", f"Processed {done_count}/{total}")

    set_task_progress(task_id, total, total, "completed", "All CVs processed")
    return {"total": total, "results": results}
