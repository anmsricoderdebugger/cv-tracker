import json
import time
import logging
import threading

from groq import Groq

from backend.config import settings

logger = logging.getLogger(__name__)

_client: Groq | None = None
_rate_lock = threading.Lock()
_last_call_time = 0.0
_MIN_INTERVAL = 0.3  # minimum seconds between API calls (across threads)


def is_llm_available() -> bool:
    key = settings.GROQ_API_KEY
    return bool(key and key.strip())


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


def _throttle():
    """Simple rate limiter to avoid hitting Groq rate limits."""
    global _last_call_time
    with _rate_lock:
        now = time.monotonic()
        elapsed = now - _last_call_time
        if elapsed < _MIN_INTERVAL:
            time.sleep(_MIN_INTERVAL - elapsed)
        _last_call_time = time.monotonic()


def call_llm(
    system_prompt: str,
    user_prompt: str,
    response_json: bool = True,
    model: str | None = None,
    max_retries: int = 5,
) -> dict | str:
    client = _get_client()
    model = model or settings.GROQ_MODEL

    kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
    }
    if response_json:
        kwargs["response_format"] = {"type": "json_object"}

    for attempt in range(max_retries):
        _throttle()
        try:
            response = client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content
            if response_json:
                return json.loads(content)
            return content
        except Exception as e:
            err_str = str(e).lower()
            is_rate_limit = "rate_limit" in err_str or "429" in err_str or "too many" in err_str
            if is_rate_limit:
                wait = min(2 ** attempt * 2, 30)
                logger.warning(f"Rate limited, waiting {wait}s (attempt {attempt + 1})")
                time.sleep(wait)
            else:
                logger.warning(f"LLM call attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise
