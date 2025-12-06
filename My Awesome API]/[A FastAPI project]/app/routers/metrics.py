from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket
from sqlalchemy.orm import Session

from app.core.cache import cache_get
from app.core.db import SessionLocal
from app.schemas.inventory import InventoryDashboard
from app.schemas.kpis import KPIs
from app.services.ai_service import get_causal_analysis
from app.services.inventory_service import build_inventory_dashboard_payload
from app.services.kpi_service import calculate_kpis
from app.services.sentiment_service import get_sentiment_summary

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/metrics/kpis/{tenant_code}", response_model=KPIs)
def get_kpis(
    tenant_code: str,
    start: date | None = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    end: date | None = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    cost_ratio: float = Query(0.65, ge=0.0, le=1.0, description="Proporción de costo asumido"),
    product: str | None = Query(None, description="Filtrar por producto"),
    channel: str | None = Query(None, description="Filtrar por canal"),
    min_amount: float | None = Query(None, description="Monto mínimo"),
    max_amount: float | None = Query(None, description="Monto máximo"),
    db: Session = Depends(get_db),
):
    try:
        kpis = calculate_kpis(
            tenant_code,
            start=start,
            end=end,
            cost_ratio=cost_ratio,
            product=product,
            channel=channel,
            min_amount=min_amount,
            max_amount=max_amount,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if kpis is None:
        raise HTTPException(status_code=404, detail="Tenant no encontrado o sin ventas en el periodo")

    return kpis


@router.get("/metrics/inventory/{tenant_code}", response_model=InventoryDashboard)
def get_inventory_dashboard(
    tenant_code: str,
    start: date | None = Query(None, description="Fecha inicio"),
    end: date | None = Query(None, description="Fecha fin"),
    product: str | None = Query(None, description="Filtrar por producto"),
    channel: str | None = Query(None, description="Filtrar por canal"),
    safety_days: int = Query(7, ge=1, le=90, description="Días de seguridad para reorden"),
):
    dashboard = build_inventory_dashboard_payload(
        tenant_code,
        start=start,
        end=end,
        product=product,
        channel=channel,
        safety_days=safety_days,
    )
    return dashboard


@router.get("/metrics/causal/{tenant_code}")
def get_causal_dashboard(
    tenant_code: str,
    start: date | None = Query(None),
    end: date | None = Query(None),
    safety_days: int = Query(7, ge=1, le=90),
    sentiment_days: int = Query(60, ge=7, le=180),
    db: Session = Depends(get_db),
):
    kpis = calculate_kpis(tenant_code, start=start, end=end, db=db)
    sentiment = get_sentiment_summary(tenant_code, days=sentiment_days)
    inventory = build_inventory_dashboard_payload(
        tenant_code,
        start=start,
        end=end,
        safety_days=safety_days,
    )
    return get_causal_analysis(
        tenant_code,
        payload={"kpis": kpis.model_dump() if kpis else {}, "sentiment": sentiment, "inventory": inventory},
    )


@router.websocket("/ws/metrics/{tenant_code}")
async def ws_metrics(websocket: WebSocket, tenant_code: str):
    """WebSocket para métricas en tiempo real."""
    await websocket.accept()
    data = cache_get(f"metrics:{tenant_code}")
    if data:
        await websocket.send_json({"type": "metrics", "payload": data})
    try:
        while True:
            msg = await websocket.receive_text()
            await websocket.send_text(f"Recibido: {msg}")
    except Exception:
        await websocket.close()
