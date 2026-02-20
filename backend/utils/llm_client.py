import json
import time
import logging
import threading

from backend.config import settings

logger = logging.getLogger(__name__)

_rate_lock = threading.Lock()
_last_call_time = 0.0
_MIN_INTERVAL = 0.3  # minimum seconds between API calls (across threads)

_vertex_initialized = False
_vertex_init_lock = threading.Lock()


def is_llm_available() -> bool:
    return bool(settings.VERTEX_PROJECT_ID and settings.VERTEX_PROJECT_ID.strip())


def _init_vertex():
    """Lazy-initialize Vertex AI SDK once per process."""
    global _vertex_initialized
    if _vertex_initialized:
        return
    with _vertex_init_lock:
        if not _vertex_initialized:
            import vertexai

            vertexai.init(
                project=settings.VERTEX_PROJECT_ID,
                location=settings.VERTEX_LOCATION,
            )
            _vertex_initialized = True


def _throttle():
    """Simple rate limiter to avoid hitting Vertex AI quota limits."""
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
    """Call Vertex AI Gemini model with retry + rate limiting.

    Args:
        system_prompt: Instructions for the model.
        user_prompt: The actual content / data to process.
        response_json: If True, request JSON output and parse the response.
        model: Vertex AI model name override (defaults to VERTEX_MODEL).
        max_retries: Maximum number of retry attempts on failure.

    Returns:
        Parsed dict if response_json=True, otherwise raw string.
    """
    from vertexai.generative_models import GenerationConfig, GenerativeModel

    _init_vertex()
    model_name = model or settings.VERTEX_MODEL

    generation_config = GenerationConfig(
        temperature=0.1,
        response_mime_type="application/json" if response_json else "text/plain",
    )

    # Combine system + user prompt (Gemini handles them as a single prompt string)
    full_prompt = f"{system_prompt}\n\n{user_prompt}"

    for attempt in range(max_retries):
        _throttle()
        try:
            vertex_model = GenerativeModel(model_name)
            response = vertex_model.generate_content(
                full_prompt,
                generation_config=generation_config,
            )
            content = response.text
            if response_json:
                return json.loads(content)
            return content
        except Exception as e:
            err_str = str(e).lower()
            is_rate_limit = (
                "429" in err_str
                or "quota" in err_str
                or "resource_exhausted" in err_str
                or "too many" in err_str
            )
            if is_rate_limit:
                wait = min(2 ** attempt * 2, 30)
                logger.warning(f"Vertex AI rate limited, waiting {wait}s (attempt {attempt + 1})")
                time.sleep(wait)
            else:
                logger.warning(f"Vertex AI call attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise
