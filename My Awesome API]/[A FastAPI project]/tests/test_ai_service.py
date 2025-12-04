import asyncio
import json


def test_get_explanation_cache_hit(monkeypatch):
    import app.services.ai_service
    import app.core.cache

    cached = {"resumen": "cached", "causa_probable": "c", "recomendacion": "r"}

    def fake_cache_get(key):
        return json.dumps(cached)

    monkeypatch.setattr(app.core.cache, 'cache_get', fake_cache_get)
    monkeypatch.setattr(app.services.ai_service, 'cache_get', fake_cache_get)

    res = asyncio.run(app.services.ai_service.get_explanation('tenant1', {'q': 'hola'}))
    assert res == cached


def test_get_explanation_cache_set_on_miss(monkeypatch):
    import app.services.ai_service
    import app.core.cache
    recorded = {}

    def fake_cache_get(key):
        return None

    def fake_cache_set(key, value, ttl=3600):
        recorded['key'] = key
        recorded['value'] = value
        recorded['ttl'] = ttl
        return True

    monkeypatch.setattr(app.core.cache, 'cache_get', fake_cache_get)
    monkeypatch.setattr(app.core.cache, 'cache_set', fake_cache_set)
    monkeypatch.setattr(app.services.ai_service, 'cache_get', fake_cache_get)
    monkeypatch.setattr(app.services.ai_service, 'cache_set', fake_cache_set)

    res = asyncio.run(app.services.ai_service.get_explanation('tenant2', {'kpis': {}}))
    # result should be a dict and cache_set should have been called
    assert isinstance(res, dict)
    assert 'key' in recorded and 'value' in recorded
