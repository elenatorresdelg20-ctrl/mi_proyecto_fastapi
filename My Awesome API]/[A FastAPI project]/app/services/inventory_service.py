"""Servicio de analítica de inventario y movimientos.

El objetivo es proveer métricas accionables sin requerir dependencias externas.
Se permiten `sales_data` inyectadas para pruebas o para operar en memoria cuando
no haya base de datos disponible.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional


@dataclass
class SaleRecord:
    """Representa una venta simplificada para cálculos de inventario."""

    product: str
    amount: float
    channel: str
    date: datetime


def _collect_sales(
    tenant_code: str,
    start: datetime,
    end: datetime,
    product: Optional[str] = None,
    channel: Optional[str] = None,
    sales_data: Optional[Iterable[SaleRecord]] = None,
):
    """Devuelve una lista de ventas filtradas.

    - Si ``sales_data`` se provee, se filtra la colección in-memory.
    - Si no, intenta consultar la base de datos usando los modelos SQLAlchemy.
    """

    if sales_data is not None:
        result: List[SaleRecord] = []
        for sale in sales_data:
            if sale.date < start or sale.date >= end:
                continue
            if product and sale.product != product:
                continue
            if channel and getattr(sale, "channel", None) != channel:
                continue
            result.append(sale)
        return result

    try:
        from sqlalchemy import and_  # type: ignore

        from app.core.db import SessionLocal
        from app.models.models import Sale, Tenant
    except Exception:
        return []

    session = SessionLocal()
    try:
        tenant = session.query(Tenant).filter(Tenant.code == tenant_code).first()
        if not tenant:
            return []

        filters = [
            Sale.tenant_id == tenant.id,
            Sale.date >= start,
            Sale.date < end,
        ]
        if product:
            filters.append(Sale.product == product)
        if channel:
            filters.append(Sale.channel == channel)

        return [
            SaleRecord(
                product=s.product or "desconocido",
                amount=float(s.amount or 0.0),
                channel=s.channel or "",
                date=s.date,
            )
            for s in session.query(Sale).filter(and_(*filters)).all()
        ]
    finally:
        session.close()


def _estimate_stock(product_counts: Dict[str, int], stock_by_product: Optional[Dict[str, int]]):
    stock_map: Dict[str, int] = {}
    for product, units_sold in product_counts.items():
        baseline = 120
        provided = (stock_by_product or {}).get(product)
        stock_map[product] = max((provided if provided is not None else baseline) - units_sold, 0)
    return stock_map


def analyze_inventory_dashboard(
    tenant_code: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    product: Optional[str] = None,
    channel: Optional[str] = None,
    safety_days: int = 7,
    stock_by_product: Optional[Dict[str, int]] = None,
    sales_data: Optional[Iterable[SaleRecord]] = None,
):
    """Calcula KPIs de inventario y genera un dashboard utilizable."""

    end_dt = end or datetime.now()
    start_dt = start or (end_dt - timedelta(days=30))

    # Aceptar fechas (date) además de datetime para mayor flexibilidad
    if not isinstance(start_dt, datetime):
        start_dt = datetime.combine(start_dt, datetime.min.time())  # type: ignore[arg-type]
    if not isinstance(end_dt, datetime):
        end_dt = datetime.combine(end_dt, datetime.min.time())  # type: ignore[arg-type]

    if start_dt > end_dt:
        raise ValueError("La fecha inicial no puede ser posterior a la final")

    sales = _collect_sales(
        tenant_code,
        start=start_dt,
        end=end_dt + timedelta(days=1),
        product=product,
        channel=channel,
        sales_data=sales_data,
    )

    if not sales:
        return {
            "summary": {
                "total_products": 0,
                "alerts": 0,
                "inventory_value": 0.0,
                "coverage_days": 0.0,
            },
            "products": [],
            "fast_movers": [],
            "slow_movers": [],
        }

    product_counts: Dict[str, int] = defaultdict(int)
    product_amounts: Dict[str, float] = defaultdict(float)
    last_sale: Dict[str, datetime] = {}
    channel_mix: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for sale in sales:
        product_counts[sale.product] += 1
        product_amounts[sale.product] += sale.amount
        last_sale[sale.product] = max(last_sale.get(sale.product, sale.date), sale.date)
        channel_mix[sale.product][sale.channel or "otros"] += 1

    stock_map = _estimate_stock(product_counts, stock_by_product)
    days_range = max((end_dt - start_dt).days, 1)

    products = []
    fast_movers = []
    slow_movers = []
    total_inventory_value = 0.0

    for product, units in product_counts.items():
        velocity = units / days_range
        avg_ticket = product_amounts[product] / max(units, 1)
        stock_units = stock_map.get(product, 0)
        coverage = stock_units / velocity if velocity > 0 else 0.0
        reorder_point = safety_days * velocity
        reorder_alert = stock_units <= reorder_point
        estimated_value = stock_units * avg_ticket
        total_inventory_value += estimated_value

        item = {
            "product": product,
            "velocity_per_day": round(velocity, 3),
            "stock_units": stock_units,
            "coverage_days": round(coverage, 2),
            "reorder_point": round(reorder_point, 2),
            "reorder_alert": reorder_alert,
            "avg_ticket": round(avg_ticket, 2),
            "revenue": round(product_amounts[product], 2),
            "last_sale_at": last_sale[product].isoformat(),
            "channel_mix": dict(channel_mix[product]),
        }

        products.append(item)
        if velocity >= 1:
            fast_movers.append(item)
        elif velocity < 0.15:
            slow_movers.append(item)

    avg_coverage = sum(p["coverage_days"] for p in products) / max(len(products), 1)

    return {
        "summary": {
            "total_products": len(products),
            "alerts": sum(1 for p in products if p["reorder_alert"]),
            "inventory_value": round(total_inventory_value, 2),
            "coverage_days": round(avg_coverage, 2),
        },
        "products": sorted(products, key=lambda p: p["revenue"], reverse=True),
        "fast_movers": fast_movers,
        "slow_movers": slow_movers,
    }


def get_inventory_movements(
    tenant_code: str,
    days: int = 30,
    product: Optional[str] = None,
    channel: Optional[str] = None,
    sales_data: Optional[Iterable[SaleRecord]] = None,
):
    """Devuelve el movimiento diario de inventario para dashboards de almacén."""

    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=days)

    sales = _collect_sales(
        tenant_code,
        start=start_dt,
        end=end_dt + timedelta(days=1),
        product=product,
        channel=channel,
        sales_data=sales_data,
    )

    daily: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

    for sale in sales:
        key = sale.date.strftime("%Y-%m-%d")
        daily[key]["units"] += 1
        daily[key]["revenue"] += sale.amount

    timeline = []
    for date_key in sorted(daily.keys()):
        timeline.append(
            {
                "date": date_key,
                "units": int(daily[date_key]["units"]),
                "revenue": round(daily[date_key]["revenue"], 2),
            }
        )

    return timeline


def build_inventory_dashboard_payload(tenant_code: str, **kwargs):
    """Crea un paquete listo para dashboards y causal analysis."""

    dashboard = analyze_inventory_dashboard(tenant_code, **kwargs)
    movements = get_inventory_movements(
        tenant_code,
        days=kwargs.get("days", 30),
        product=kwargs.get("product"),
        channel=kwargs.get("channel"),
        sales_data=kwargs.get("sales_data"),
    )

    dashboard["movements"] = movements
    return dashboard
