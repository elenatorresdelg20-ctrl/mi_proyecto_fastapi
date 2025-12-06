import json
from hashlib import sha256
from typing import Any, Dict, List, Optional

from app.core.cache import cache_get, cache_set


def _make_cache_key(tenant_code: str, payload: Any) -> str:
    h = sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return f"explain:{tenant_code}:{h}"


def _summarize_kpis(kpis: Dict[str, Any]) -> str:
    """Genera un resumen breve y determinista a partir de KPIs enviados."""
    if not kpis:
        return "Sin métricas disponibles para generar conclusiones."

    ventas = kpis.get("ventas")
    ticket = kpis.get("ticket_promedio")
    margen = kpis.get("margen")
    transacciones = kpis.get("transacciones")

    partes: List[str] = []
    if ventas is not None:
        partes.append(f"ventas totales por {ventas:,.2f}")
    if transacciones is not None:
        partes.append(f"{transacciones} transacciones")
    if ticket is not None:
        partes.append(f"ticket promedio de {ticket:,.2f}")
    if margen is not None:
        partes.append(f"margen estimado de {margen:,.2f}")

    return "; ".join(partes) if partes else "Sin métricas disponibles para generar conclusiones."


def _summarize_sentiment(sentiment: Optional[Dict[str, Any]]) -> str:
    if not sentiment:
        return "No hay feedback reciente analizado."

    total = sentiment.get("total_feedback", 0)
    polarity = sentiment.get("avg_polarity", 0)
    satisfaction = sentiment.get("avg_satisfaction", 0)

    tendencia = "neutral"
    if polarity > 0.2:
        tendencia = "positiva"
    elif polarity < -0.2:
        tendencia = "negativa"

    return (
        f"Se analizaron {total} comentarios; la tendencia es {tendencia} "
        f"con satisfacción media de {satisfaction:.1f} y polaridad promedio de {polarity:.2f}."
    )


def _build_ai_response(tenant_code: str, payload: Any) -> Dict[str, Any]:
    """Crea una respuesta explicativa usando reglas deterministas."""

    kpis = payload.get("kpis", {}) if isinstance(payload, dict) else {}
    sentiment = payload.get("sentiment", {}) if isinstance(payload, dict) else {}

    resumen_kpis = _summarize_kpis(kpis)
    resumen_sentimiento = _summarize_sentiment(sentiment)

    puntos_fuertes: List[str] = []
    alertas: List[str] = []

    margen = kpis.get("margen")
    ventas = kpis.get("ventas")
    ticket = kpis.get("ticket_promedio")

    if margen is not None and ventas:
        margen_pct = (margen / ventas) * 100 if ventas else 0
        if margen_pct >= 30:
            puntos_fuertes.append("La rentabilidad está por encima del 30%.")
        else:
            alertas.append("El margen está por debajo del 30%, conviene revisar costos.")

    if ticket and ticket > 0:
        puntos_fuertes.append(f"El ticket promedio es {ticket:,.2f}, se puede potenciar upselling.")

    if sentiment.get("avg_polarity", 0) < -0.1:
        alertas.append("El feedback reciente es negativo, priorizar soporte y mejoras de producto.")

    resumen = f"KPIs: {resumen_kpis}. Sentimiento: {resumen_sentimiento}"

    causa_probable = "Tendencia explicada por comportamiento de ventas y percepción del cliente."
    if alertas:
        causa_probable = " ".join(alertas)
    elif puntos_fuertes:
        causa_probable = " ".join(puntos_fuertes)

    recomendacion = "Enfocar acciones en eficiencia operativa y experiencia del cliente."
    if alertas and puntos_fuertes:
        recomendacion = (
            "Mantener los puntos fuertes detectados y ejecutar un plan de mejora para las alertas."
        )
    elif alertas:
        recomendacion = "Priorizar la resolución de las alertas identificadas y medir impacto semanal."
    elif puntos_fuertes:
        recomendacion = "Acelerar iniciativas asociadas a los puntos fuertes para capitalizarlos."

    return {
        "tenant": tenant_code,
        "resumen": resumen,
        "causa_probable": causa_probable,
        "recomendacion": recomendacion,
        "puntos_fuertes": puntos_fuertes,
        "alertas": alertas,
    }


async def get_explanation(tenant_code: str, payload):
    """Obtiene explicación, usando cache Redis si está disponible.

    - Clave de cache: `explain:{tenant}:{sha256(payload)}`
    - En hit devuelve el JSON deserializado
    - En miss genera una respuesta determinista y la guarda en cache
    """
    key = _make_cache_key(tenant_code, payload)
    cached = cache_get(key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    result = _build_ai_response(tenant_code, payload if isinstance(payload, dict) else {})

    try:
        cache_set(key, json.dumps(result), ttl=3600)
    except Exception:
        pass

    return result
