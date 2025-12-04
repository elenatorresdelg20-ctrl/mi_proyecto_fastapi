import os
from typing import Optional

redis_url = os.environ.get("REDIS_URL")

_redis = None


def get_redis():
    """Lazily import and return a redis client or None if not configured."""
    global _redis
    if _redis is not None:
        return _redis
    if not redis_url:
        return None
    try:
        import redis
    except Exception:
        return None
    _redis = redis.from_url(redis_url, decode_responses=True)
    return _redis


def cache_get(key: str) -> Optional[str]:
    r = get_redis()
    if not r:
        return None
    try:
        return r.get(key)
    except Exception:
        return None


def cache_set(key: str, value: str, ttl: int = 3600) -> bool:
    r = get_redis()
    if not r:
        return False
    try:
        r.set(key, value, ex=ttl)
        return True
    except Exception:
        return False
