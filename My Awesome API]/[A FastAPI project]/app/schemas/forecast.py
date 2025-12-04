from pydantic import BaseModel
from datetime import date
from typing import List, Optional


class ForecastPoint(BaseModel):
    """Un punto de pronóstico de ventas."""
    date: date
    expected_amount: float


class ProductChannelForecast(BaseModel):
    """Análisis de ventas por producto o canal."""
    name: str
    total: float
    count: int
    avg: float
    pct: float  # Porcentaje del total


class SeasonalityFactor(BaseModel):
    """Factor de seasonalidad por día de semana."""
    day: str
    factor: float


class ForecastMetadata(BaseModel):
    """Metadata del pronóstico."""
    historical_avg: float
    std_dev: float
    trend: str  # "up", "down", "stable"
    model: str  # "linear_trend", "moving_average", "hybrid"
    confidence: float  # 0-1


class ForecastOut(BaseModel):
    """Respuesta de pronóstico de ventas con análisis detallado."""
    forecast: List[ForecastPoint]
    drop_pct: float  # % de caída esperada vs histórico
    alert: float  # Valor de alerta (0 = sin alerta, >0 = alerta)
    products: Optional[List[ProductChannelForecast]] = None  # Análisis por producto
    channels: Optional[List[ProductChannelForecast]] = None  # Análisis por canal
    seasonality: Optional[List[SeasonalityFactor]] = None  # Factores de seasonalidad
    meta: Optional[ForecastMetadata] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "forecast": [
                    {"date": "2025-12-04", "expected_amount": 5000.0},
                    {"date": "2025-12-05", "expected_amount": 5200.0}
                ],
                "drop_pct": -5.5,
                "alert": 0.0,
                "products": [
                    {"name": "iPhone 15", "total": 250000, "count": 50, "avg": 5000, "pct": 45.5},
                    {"name": "iPad Pro", "total": 200000, "count": 30, "avg": 6667, "pct": 36.4}
                ],
                "channels": [
                    {"name": "Online", "total": 300000, "count": 50, "avg": 6000, "pct": 54.5},
                    {"name": "Tienda Física", "total": 250000, "count": 30, "avg": 8333, "pct": 45.5}
                ],
                "seasonality": [
                    {"day": "Monday", "factor": 0.150},
                    {"day": "Friday", "factor": 0.175},
                    {"day": "Saturday", "factor": 0.200}
                ],
                "meta": {
                    "historical_avg": 5000.0,
                    "std_dev": 800.0,
                    "trend": "up",
                    "model": "hybrid",
                    "confidence": 0.85
                }
            }
        }


