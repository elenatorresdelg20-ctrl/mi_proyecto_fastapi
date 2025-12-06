"""Cálculo de KPIs de ventas a partir de los registros almacenados."""

from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.models import Sale, Tenant
from app.schemas.kpis import KPIs


def calculate_kpis(
    tenant_code: str,
    start: Optional[date] = None,
    end: Optional[date] = None,
    cost_ratio: float = 0.65,
    db: Optional[Session] = None,
) -> Optional[KPIs]:
    """Calcula KPIs clave para un tenant.

    - **ventas**: suma de `amount` en el periodo.
    - **transacciones**: número de ventas en el periodo.
    - **ticket_promedio**: ventas / transacciones (0 si no hay transacciones).
    - **margen**: ventas menos el costo estimado (usando ``cost_ratio``).

    ``cost_ratio`` representa la proporción de las ventas que se asume como costo
    (0.65 equivale a un margen bruto del 35%).
    """

    own_session = False
    session = db
    if session is None:
        session = SessionLocal()
        own_session = True

    try:
        tenant = session.query(Tenant).filter(Tenant.code == tenant_code).first()
        if not tenant:
            return None

        end_date = end or date.today()
        start_date = start or (end_date - timedelta(days=30))

        if start_date > end_date:
            raise ValueError("La fecha inicial no puede ser posterior a la fecha final")

        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date + timedelta(days=1), datetime.min.time())

        transacciones, ventas = session.query(
            func.count(Sale.id),
            func.coalesce(func.sum(Sale.amount), 0.0),
        ).filter(
            Sale.tenant_id == tenant.id,
            Sale.date >= start_dt,
            Sale.date < end_dt,
        ).one()

        ventas = float(ventas or 0.0)
        transacciones = int(transacciones or 0)

        ticket_promedio = ventas / transacciones if transacciones else 0.0

        normalized_cost_ratio = min(max(cost_ratio, 0.0), 1.0)
        costo_estimado = ventas * normalized_cost_ratio
        margen = max(ventas - costo_estimado, 0.0)

        return KPIs(
            ventas=round(ventas, 2),
            transacciones=transacciones,
            ticket_promedio=round(ticket_promedio, 2),
            margen=round(margen, 2),
        )
    finally:
        if own_session:
            session.close()
