import json
from hashlib import sha256
from typing import Any

from app.core.cache import cache_get, cache_set


def _make_cache_key(tenant_code: str, payload: Any) -> str:
    h = sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return f"explain:{tenant_code}:{h}"


async def get_explanation(tenant_code: str, payload):
    """Obtiene explicación, usando cache Redis si está disponible.

    - dry cache key is `explain:{tenant}:{sha256(payload)}`
    - if cache hit, devuelve el JSON deserializado
    - otherwise genera (placeholder) y guarda en cache
    """
    key = _make_cache_key(tenant_code, payload)
    cached = cache_get(key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    # Placeholder logic: aquí iría la llamada al proveedor IA
    result = {"resumen": "Ejemplo", "causa_probable": "Ejemplo", "recomendacion": "Ejemplo"}

    try:
        cache_set(key, json.dumps(result), ttl=3600)
    except Exception:
        pass

    return result
