from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket
from sqlalchemy.orm import Session

from app.core.cache import cache_get
from app.core.db import SessionLocal
from app.schemas.kpis import KPIs
from app.services.kpi_service import calculate_kpis

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
    db: Session = Depends(get_db),
):
    try:
        kpis = calculate_kpis(tenant_code, start=start, end=end, cost_ratio=cost_ratio, db=db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if kpis is None:
        raise HTTPException(status_code=404, detail="Tenant no encontrado o sin ventas en el periodo")

    return kpis


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
