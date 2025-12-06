from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
import hashlib

from app.dependencies.tenant import get_db, verify_tenant_api_key
from app.schemas.explain import ExplainRequest, ExplainResponse
from app.services.ai_client import AIClient, cache_get, cache_set
from app.core.rate_limiter import require_rate_allowed

router = APIRouter()
ai_client = AIClient()


@router.post("/explain/{tenant_code}", response_model=ExplainResponse)
async def explain_data(
    tenant_code: str,
    payload: ExplainRequest,
    request: Request,
    db: Session = Depends(get_db),
    tenant=Depends(verify_tenant_api_key),
):
    # Rate limit per tenant + client IP
    client_ip = request.client.host if request.client else "unknown"
    require_rate_allowed(tenant_code, client_ip)

    from app.utils.helpers import build_explain_prompt  # optional if implemented elsewhere

    context = {"kpis": payload.kpis, "top_changes": payload.top_changes or [], "anomalies": payload.anomalies or []}
    prompt = build_explain_prompt(context)
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()

    cached = cache_get(prompt_hash)
    if cached:
        parts = [p.strip() for p in cached.split("\n\n") if p.strip()]
        resumen = parts[0] if len(parts) > 0 else ""
        causa = parts[1] if len(parts) > 1 else ""
        recomendacion = parts[2] if len(parts) > 2 else ""
        meta = {"model": "cache", "latency": 0.0, "cost_estimate": 0.0}
        return ExplainResponse(resumen=resumen, causa_probable=causa, recomendacion=recomendacion, meta=meta)

    ai_res = await ai_client.explain(prompt, max_tokens=250)

    if not ai_res.get("text") or ai_res.get("confidence", 0) < 0.5:
        resumen = f"Ventas totales: {payload.kpis.get('ventas_actuales', 'N/A')}, transacciones: {payload.kpis.get('transacciones_actuales', 'N/A')}.""
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
        cache_set(prompt_hash, text)
    except Exception:
        pass

    meta = {"model": ai_res.get("model"), "latency": ai_res.get("latency"), "cost_estimate": ai_res.get("cost_estimate")}
    return ExplainResponse(resumen=resumen, causa_probable=causa, recomendacion=recomendacion, meta=meta)
