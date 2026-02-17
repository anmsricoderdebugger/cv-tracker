import json

import redis

from backend.config import settings

_redis: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


def set_task_progress(task_id: str, current: int, total: int, status: str, message: str = ""):
    r = get_redis()
    r.hset(
        f"task:{task_id}:progress",
        mapping={"current": current, "total": total, "status": status, "message": message},
    )
    r.expire(f"task:{task_id}:progress", 3600)


def get_task_progress(task_id: str) -> dict | None:
    r = get_redis()
    data = r.hgetall(f"task:{task_id}:progress")
    if not data:
        return None
    return {
        "current": int(data.get("current", 0)),
        "total": int(data.get("total", 0)),
        "status": data.get("status", "unknown"),
        "message": data.get("message", ""),
    }


def publish_event(channel: str, event: dict):
    r = get_redis()
    r.publish(channel, json.dumps(event))
