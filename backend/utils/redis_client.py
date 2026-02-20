"""Redis client with graceful fallback to in-memory storage.

On hosting platforms without Redis (e.g. Render free plan), the app still
starts and works correctly. Features that rely on Redis (OAuth CSRF state,
task progress) fall back to thread-safe in-memory dictionaries.

Set REDIS_URL in the environment to enable persistent Redis storage.
"""

import json
import logging
import threading
import time

import redis

from backend.config import settings

logger = logging.getLogger(__name__)

_redis: redis.Redis | None = None
_redis_available: bool | None = None  # None = not yet checked
_redis_lock = threading.Lock()

# ---------------------------------------------------------------------------
# In-memory fallbacks (used when Redis is unavailable)
# ---------------------------------------------------------------------------
_mem_lock = threading.Lock()
_mem_store: dict[str, tuple[str, float]] = {}  # key -> (value, expires_at)
_mem_progress: dict[str, dict] = {}


def _cleanup_expired():
    """Remove expired keys from the in-memory store."""
    now = time.monotonic()
    with _mem_lock:
        expired = [k for k, (_, exp) in _mem_store.items() if exp and exp < now]
        for k in expired:
            del _mem_store[k]


def is_redis_available() -> bool:
    """Return True if Redis is reachable. Result is cached after first check."""
    global _redis_available
    if _redis_available is not None:
        return _redis_available
    with _redis_lock:
        if _redis_available is not None:
            return _redis_available
        try:
            r = redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=2)
            r.ping()
            _redis_available = True
            logger.info("Redis connection established.")
        except Exception as e:
            _redis_available = False
            logger.warning(f"Redis unavailable — using in-memory fallback. ({e})")
    return _redis_available


def get_redis() -> redis.Redis:
    """Return a connected Redis client. Raises if Redis is not available."""
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


# ---------------------------------------------------------------------------
# Key/value with TTL (used for OAuth state)
# ---------------------------------------------------------------------------

def setex(key: str, ttl_seconds: int, value: str):
    """Set key with expiry — Redis or in-memory fallback."""
    if is_redis_available():
        get_redis().setex(key, ttl_seconds, value)
    else:
        with _mem_lock:
            _mem_store[key] = (value, time.monotonic() + ttl_seconds)


def exists(key: str) -> bool:
    """Check if key exists and has not expired."""
    if is_redis_available():
        return bool(get_redis().exists(key))
    _cleanup_expired()
    with _mem_lock:
        return key in _mem_store


def delete(key: str):
    """Delete a key."""
    if is_redis_available():
        get_redis().delete(key)
    else:
        with _mem_lock:
            _mem_store.pop(key, None)


# ---------------------------------------------------------------------------
# Task progress (used by CV processing pipeline)
# ---------------------------------------------------------------------------

def set_task_progress(task_id: str, current: int, total: int, status: str, message: str = ""):
    data = {"current": current, "total": total, "status": status, "message": message}
    if is_redis_available():
        r = get_redis()
        r.hset(f"task:{task_id}:progress", mapping=data)
        r.expire(f"task:{task_id}:progress", 3600)
    else:
        with _mem_lock:
            _mem_progress[task_id] = data


def get_task_progress(task_id: str) -> dict | None:
    if is_redis_available():
        r = get_redis()
        data = r.hgetall(f"task:{task_id}:progress")
        if not data:
            return None
    else:
        with _mem_lock:
            data = _mem_progress.get(task_id)
        if not data:
            return None

    return {
        "current": int(data.get("current", 0)),
        "total": int(data.get("total", 0)),
        "status": data.get("status", "unknown"),
        "message": data.get("message", ""),
    }


def publish_event(channel: str, event: dict):
    """Publish a Redis pub/sub event (no-op if Redis unavailable)."""
    if is_redis_available():
        get_redis().publish(channel, json.dumps(event))
    else:
        logger.debug(f"Redis unavailable — skipping pub/sub event on channel '{channel}'")
