import logging
from pathlib import Path

from watchdog.events import FileSystemEventHandler

from backend.config import settings
from backend.utils.redis_client import publish_event

logger = logging.getLogger(__name__)


class CVFolderHandler(FileSystemEventHandler):
    def __init__(self, folder_id: str):
        self.folder_id = folder_id
        self.allowed_exts = set(settings.ALLOWED_EXTENSIONS)

    def _is_cv_file(self, path: str) -> bool:
        return Path(path).suffix.lower() in self.allowed_exts

    def on_created(self, event):
        if event.is_directory:
            return
        if self._is_cv_file(event.src_path):
            logger.info(f"New CV detected: {event.src_path} in folder {self.folder_id}")
            publish_event(
                f"folder:{self.folder_id}:events",
                {"type": "created", "path": event.src_path, "folder_id": self.folder_id},
            )

    def on_modified(self, event):
        if event.is_directory:
            return
        if self._is_cv_file(event.src_path):
            logger.info(f"CV modified: {event.src_path} in folder {self.folder_id}")
            publish_event(
                f"folder:{self.folder_id}:events",
                {"type": "modified", "path": event.src_path, "folder_id": self.folder_id},
            )

    def on_deleted(self, event):
        if event.is_directory:
            return
        if self._is_cv_file(event.src_path):
            logger.info(f"CV deleted: {event.src_path} in folder {self.folder_id}")
            publish_event(
                f"folder:{self.folder_id}:events",
                {"type": "deleted", "path": event.src_path, "folder_id": self.folder_id},
            )
