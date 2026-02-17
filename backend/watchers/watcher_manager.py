import logging
import threading

from watchdog.observers import Observer

from backend.watchers.folder_watcher import CVFolderHandler

logger = logging.getLogger(__name__)

_observers: dict[str, Observer] = {}
_lock = threading.Lock()


def start_watching(folder_id: str, folder_path: str) -> bool:
    with _lock:
        if folder_id in _observers:
            logger.info(f"Already watching folder {folder_id}")
            return False

        handler = CVFolderHandler(folder_id)
        observer = Observer()
        observer.schedule(handler, folder_path, recursive=False)
        observer.daemon = True
        observer.start()
        _observers[folder_id] = observer
        logger.info(f"Started watching folder {folder_id}: {folder_path}")
        return True


def stop_watching(folder_id: str) -> bool:
    with _lock:
        observer = _observers.pop(folder_id, None)
        if observer:
            observer.stop()
            observer.join(timeout=5)
            logger.info(f"Stopped watching folder {folder_id}")
            return True
        return False


def is_watching(folder_id: str) -> bool:
    return folder_id in _observers


def stop_all():
    with _lock:
        for folder_id, observer in _observers.items():
            observer.stop()
            observer.join(timeout=5)
            logger.info(f"Stopped watching folder {folder_id}")
        _observers.clear()
