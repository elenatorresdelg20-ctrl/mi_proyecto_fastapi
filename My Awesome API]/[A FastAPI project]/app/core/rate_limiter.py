from typing import Tuple

from fastapi import HTTPException

from .cache import get_redis
from .config import get_settings

settings = get_settings()
RATE_LIMIT = settings.rate_limit
RATE_PERIOD = settings.rate_limit_period


def check_rate(tenant_code: str, ip: str) -> Tuple[bool, int, int]:
    """Return (allowed, remaining, reset_seconds).

    Uses a simple fixed-window counter keyed by tenant+ip in Redis.
    If Redis is not configured, allows all requests.
    """
    r = get_redis()
    if not r:
        return True, RATE_LIMIT, 0

    key = f"rl:{tenant_code}:{ip}"
    try:
        current = r.incr(key)
        if current == 1:
            r.expire(key, RATE_PERIOD)
        ttl = r.ttl(key) or 0
        if current > RATE_LIMIT:
            return False, 0, ttl
        return True, RATE_LIMIT - int(current), ttl
    except Exception:
        # On Redis error, fail-open
        return True, RATE_LIMIT, 0


def require_rate_allowed(tenant_code: str, ip: str):
    allowed, remaining, reset = check_rate(tenant_code, ip)
    if not allowed:
        raise HTTPException(status_code=429, detail=f"Rate limit exceeded. Retry in {reset}s")
    return remaining, reset
