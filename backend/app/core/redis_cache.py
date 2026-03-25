import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

CACHE_7_DAYS = 7 * 24 * 60 * 60  # seconds


def _get_client():
    """Lazily create a Redis client. Returns None if REDIS_URL is not set."""
    try:
        from app.core.config import settings
        url = getattr(settings, "REDIS_URL", None)
        if not url:
            return None
        import redis as redis_lib
        client = redis_lib.from_url(url, decode_responses=True, socket_connect_timeout=3)
        client.ping()
        return client
    except Exception as e:
        logger.warning("Redis unavailable, caching disabled: %s", e)
        return None


_client = None
_client_checked = False


def _redis():
    global _client, _client_checked
    if not _client_checked:
        _client = _get_client()
        _client_checked = True
    return _client


def cache_get(key: str) -> Optional[Any]:
    """Return parsed JSON value for key, or None on miss/error."""
    r = _redis()
    if r is None:
        return None
    try:
        raw = r.get(key)
        return json.loads(raw) if raw is not None else None
    except Exception as e:
        logger.warning("Redis GET error for key %s: %s", key, e)
        return None


def cache_set(key: str, value: Any, ttl: int = CACHE_7_DAYS) -> None:
    """Serialize value to JSON and store with TTL. Silently skips on error."""
    r = _redis()
    if r is None:
        return
    try:
        r.set(key, json.dumps(value), ex=ttl)
    except Exception as e:
        logger.warning("Redis SET error for key %s: %s", key, e)
