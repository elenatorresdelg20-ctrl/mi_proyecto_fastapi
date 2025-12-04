import pytest
from fastapi import HTTPException


class FakeRedis:
    def __init__(self):
        self.counters = {}
        self.expiries = {}

    def incr(self, key):
        v = self.counters.get(key, 0) + 1
        self.counters[key] = v
        return v

    def expire(self, key, seconds):
        self.expiries[key] = seconds
        return True

    def ttl(self, key):
        return self.expiries.get(key, -1)


def test_allow_when_no_redis(monkeypatch):
    # Simulate no redis configured
    import importlib
    rate_limiter = importlib.import_module('app.core.rate_limiter')
    monkeypatch.setattr(rate_limiter, 'get_redis', lambda: None)
    allowed, remaining, reset = rate_limiter.check_rate('tenant1', '1.2.3.4')
    assert allowed is True
    assert remaining == rate_limiter.RATE_LIMIT


def test_rate_limit_exceeded(monkeypatch):
    import importlib
    rate_limiter = importlib.import_module('app.core.rate_limiter')
    fake = FakeRedis()
    # set counter so that next incr will exceed
    fake.counters['rl:tenantX:9.9.9.9'] = rate_limiter.RATE_LIMIT
    monkeypatch.setattr(rate_limiter, 'get_redis', lambda: fake)

    allowed, remaining, reset = rate_limiter.check_rate('tenantX', '9.9.9.9')
    assert allowed is False
    assert remaining == 0
    assert isinstance(reset, int)


def test_require_rate_allowed_raises(monkeypatch):
    import importlib
    rate_limiter = importlib.import_module('app.core.rate_limiter')
    fake = FakeRedis()
    fake.counters['rl:tenantY:8.8.8.8'] = rate_limiter.RATE_LIMIT
    monkeypatch.setattr(rate_limiter, 'get_redis', lambda: fake)

    with pytest.raises(HTTPException):
        rate_limiter.require_rate_allowed('tenantY', '8.8.8.8')
