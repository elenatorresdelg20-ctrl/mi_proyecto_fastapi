from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import hashlib
from typing import Any

from app.core.security import get_tenant_context
from app.dependencies import get_db
from app.schemas.explain import ExplainRequest, ExplainResponse
from app.services.ai_client import AIClient, cache_get, cache_set
from app.schemas.dashboard import AnalysisDashboardResponse, BreakdownRow, KpiCard, TrendPoint

router = APIRouter()
ai_client = AIClient()


@router.get("/api/analysis/{tenant_code}", response_model=AnalysisDashboardResponse)
async def analysis_overview(tenant_code: str, ctx=Depends(get_tenant_context)):
    """Entrega los KPIs y gráficas base que el frontend mostraba en memoria."""

    tenant = ctx["tenant"]
    kpis = [
        KpiCard(label="Ingresos", value=125000.0, change=5.2),
        KpiCard(label="Ticket promedio", value=320.5, change=-1.4),
        KpiCard(label="Órdenes", value=482, change=3.1),
    ]
    trend = [
        TrendPoint(label="Semana 1", value=28000),
        TrendPoint(label="Semana 2", value=30500),
        TrendPoint(label="Semana 3", value=31800),
        TrendPoint(label="Semana 4", value=34650),
    ]
    breakdown = [
        BreakdownRow(name="Online", value=72000, change=4.2),
        BreakdownRow(name="Retail", value=41000, change=2.1),
        BreakdownRow(name="Wholesale", value=12000, change=-0.8),
    ]

    return AnalysisDashboardResponse(tenant=tenant.code, kpis=kpis, trend=trend, breakdown=breakdown)
@router.post("/explain/{tenant_code}", response_model=ExplainResponse)
async def explain_data(
    tenant_code: str,
    payload: ExplainRequest,
    db: Session = Depends(get_db),
    ctx=Depends(get_tenant_context),
):
    tenant = ctx["tenant"]

    from app.utils.helpers import build_explain_prompt  # optional if implemented elsewhere

    context = {"kpis": payload.kpis, "top_changes": payload.top_changes or [], "anomalies": payload.anomalies or []}
    prompt = build_explain_prompt(context)
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
    cache_key = f"explain:{tenant.code}:{prompt_hash}"

    cached = cache_get(cache_key)
    if cached:
        parts = [p.strip() for p in cached.split("\n\n") if p.strip()]
        resumen = parts[0] if len(parts) > 0 else ""
        causa = parts[1] if len(parts) > 1 else ""
        recomendacion = parts[2] if len(parts) > 2 else ""
        meta = {"model": "cache", "latency": 0.0, "cost_estimate": 0.0}
        return ExplainResponse(resumen=resumen, causa_probable=causa, recomendacion=recomendacion, meta=meta)

    ai_res = await ai_client.explain(prompt, max_tokens=250)

    if not ai_res.get("text") or ai_res.get("confidence", 0) < 0.5:
        resumen = f"Ventas totales: {payload.kpis.get('ventas_actuales', 'N/A')}, transacciones: {payload.kpis.get('transacciones_actuales', 'N/A')}."
        causa = "Se detectó una variación en los principales productos; revisar promociones y stock."
        recomendacion = "Revisar top 5 productos y ajustar inventario/promociones."
        meta = {"model": "fallback", "latency": ai_res.get("latency", 0.0), "cost_estimate": ai_res.get("cost_estimate", 0.0)}
        return ExplainResponse(resumen=resumen, causa_probable=causa, recomendacion=recomendacion, meta=meta)

    text = ai_res["text"].strip()
    if "\n\n" in text:
        parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    else:
        parts = [p.strip() for p in text.split("\n") if p.strip()]

    resumen = parts[0] if len(parts) > 0 else ""
    causa = parts[1] if len(parts) > 1 else ""
    recomendacion = parts[2] if len(parts) > 2 else ""

    try:
        cache_set(cache_key, text)
    except Exception:
        pass

    meta = {"model": ai_res.get("model"), "latency": ai_res.get("latency"), "cost_estimate": ai_res.get("cost_estimate")}
    return ExplainResponse(resumen=resumen, causa_probable=causa, recomendacion=recomendacion, meta=meta)
