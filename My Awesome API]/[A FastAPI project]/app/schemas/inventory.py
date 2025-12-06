from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel, Field


class InventoryProduct(BaseModel):
    product: str
    velocity_per_day: float = Field(..., description="Velocidad de venta por día")
    stock_units: int
    coverage_days: float
    reorder_point: float
    reorder_alert: bool
    avg_ticket: float
    revenue: float
    last_sale_at: datetime
    channel_mix: Dict[str, int]


class InventorySummary(BaseModel):
    total_products: int
    alerts: int
    inventory_value: float
    coverage_days: float


class InventoryDashboard(BaseModel):
    summary: InventorySummary
    products: List[InventoryProduct]
    fast_movers: List[InventoryProduct]
    slow_movers: List[InventoryProduct]
    movements: List[Dict]
