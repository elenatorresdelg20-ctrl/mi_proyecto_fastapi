"""
Forecast Service: Pronósticos de ventas basados en series temporales.

Métodos:
- Promedio móvil simple (SMA)
- Tendencia (regresión lineal)
- Detección de anomalías (desviación estándar)
- Análisis por producto y canal
- Seasonalidad por día de semana
"""

from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.models import Sale, Tenant
from app.schemas.forecast import (
    ForecastMetadata,
    ForecastOut,
    ForecastPoint,
    ProductChannelForecast,
    SeasonalityFactor,
)


def _get_daily_sales(db: Session, tenant_id: int, days: int = 90) -> Dict[str, float]:
    """Obtiene ventas diarias agregadas para los últimos N días."""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    results = db.query(
        func.date(Sale.date).label("day"),
        func.sum(Sale.amount).label("total")
    ).filter(
        Sale.tenant_id == tenant_id,
        Sale.date >= cutoff_date
    ).group_by(
        func.date(Sale.date)
    ).all()
    
    daily_sales = {str(row[0]): row[1] for row in results}
    return daily_sales


def _get_sales_by_product(db: Session, tenant_id: int, days: int = 90) -> Dict[str, Dict]:
    """Obtiene análisis de ventas por producto."""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    results = db.query(
        Sale.product,
        func.sum(Sale.amount).label("total"),
        func.count(Sale.id).label("count"),
        func.avg(Sale.amount).label("avg_amount")
    ).filter(
        Sale.tenant_id == tenant_id,
        Sale.date >= cutoff_date
    ).group_by(Sale.product).all()
    
    products = {}
    for product, total, count, avg in results:
        products[product] = {
            "total": float(total),
            "count": count,
            "avg": float(avg),
            "pct": 0
        }
    
    total_sales = sum(p["total"] for p in products.values())
    for product in products:
        products[product]["pct"] = (products[product]["total"] / total_sales * 100) if total_sales > 0 else 0
    
    return products


def _get_sales_by_channel(db: Session, tenant_id: int, days: int = 90) -> Dict[str, Dict]:
    """Obtiene análisis de ventas por canal."""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    results = db.query(
        Sale.channel,
        func.sum(Sale.amount).label("total"),
        func.count(Sale.id).label("count"),
        func.avg(Sale.amount).label("avg_amount")
    ).filter(
        Sale.tenant_id == tenant_id,
        Sale.date >= cutoff_date
    ).group_by(Sale.channel).all()
    
    channels = {}
    for channel, total, count, avg in results:
        channels[channel] = {
            "total": float(total),
            "count": count,
            "avg": float(avg),
            "pct": 0
        }
    
    total_sales = sum(c["total"] for c in channels.values())
    for channel in channels:
        channels[channel]["pct"] = (channels[channel]["total"] / total_sales * 100) if total_sales > 0 else 0
    
    return channels


def _calculate_seasonality(db: Session, tenant_id: int, days: int = 90) -> Dict[str, float]:
    """Calcula factores de seasonalidad por día de semana."""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    sales = db.query(Sale).filter(
        Sale.tenant_id == tenant_id,
        Sale.date >= cutoff_date
    ).all()
    
    day_totals = {day: 0.0 for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
    day_counts = {day: 0 for day in day_totals.keys()}
    
    for sale in sales:
        day_name = sale.date.strftime("%A")
        day_totals[day_name] += sale.amount
        day_counts[day_name] += 1
    
    total_sales = sum(day_totals.values())
    seasonality = {}
    
    for day in day_totals:
        if day_counts[day] > 0:
            seasonality[day] = day_totals[day] / total_sales if total_sales > 0 else (1/7)
        else:
            seasonality[day] = 1/7
    
    return seasonality


def _calculate_moving_average(values: List[float], window: int = 7) -> List[float]:
    """Calcula promedio móvil simple."""
    ma = []
    for i in range(len(values)):
        if i < window:
            ma.append(sum(values[:i+1]) / (i + 1))
        else:
            ma.append(sum(values[i-window+1:i+1]) / window)
    return ma


def _calculate_trend(values: List[float]) -> Tuple[float, float]:
    """Calcula tendencia lineal (slope, intercept)."""
    if len(values) < 2:
        return 0.0, values[0] if values else 0.0
    
    n = len(values)
    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(values) / n
    
    numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
    
    slope = numerator / denominator if denominator != 0 else 0.0
    intercept = y_mean - slope * x_mean
    
    return slope, intercept


def _calculate_std_dev(values: List[float]) -> float:
    """Calcula desviación estándar."""
    if len(values) < 2:
        return 0.0

    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return variance ** 0.5


def _detect_anomalies(values: List[float], threshold: float = 2.0) -> float:
    """Detecta anomalías (% de valores fuera de N desviaciones estándar)."""
    if len(values) < 2:
        return 0.0
    
    mean = sum(values) / len(values)
    std_dev = _calculate_std_dev(values)
    
    if std_dev == 0:
        return 0.0
    
    anomaly_count = sum(1 for v in values if abs(v - mean) > threshold * std_dev)
    return (anomaly_count / len(values)) * 100


def _trend_label(slope: float, avg: float) -> str:
    """Simplifica la tendencia."""
    if avg == 0:
        return "stable"
    pct = slope / max(avg, 1e-6)
    if pct > 0.01:
        return "up"
    if pct < -0.01:
        return "down"
    return "stable"


def _confidence_score(std_dev: float, mean: float) -> float:
    """Devuelve una confianza 0-1 basada en la variabilidad."""
    if mean <= 0:
        return 0.0
    ratio = std_dev / mean
    confidence = max(0.0, 1.0 - ratio)
    return round(min(confidence, 1.0), 3)


def get_forecast_data(tenant_code: str, start: str, end: str, db: Session | None = None) -> ForecastOut:
    """Genera pronóstico de ventas con análisis detallado y metadata de confianza."""
    owns_session = db is None
    db = db or SessionLocal()

    try:
        tenant = db.query(Tenant).filter(Tenant.code == tenant_code).first()
        if not tenant:
            return ForecastOut(forecast=[], drop_pct=0.0, alert=0.0)

        daily_sales = _get_daily_sales(db, tenant.id, days=90)

        if not daily_sales:
            return ForecastOut(forecast=[], drop_pct=0.0, alert=0.0)

        sorted_dates = sorted(daily_sales.keys())
        historical_values = [daily_sales[d] for d in sorted_dates]

        ma_values = _calculate_moving_average(historical_values, window=7)
        slope, intercept = _calculate_trend(historical_values)
        anomaly_pct = _detect_anomalies(historical_values)

        avg_daily_sales = sum(historical_values) / len(historical_values)
        std_dev = _calculate_std_dev(historical_values)

        products_analysis = _get_sales_by_product(db, tenant.id)
        channels_analysis = _get_sales_by_channel(db, tenant.id)
        seasonality = _calculate_seasonality(db, tenant.id)

        try:
            start_date = datetime.strptime(start, "%Y-%m-%d").date()
            end_date = datetime.strptime(end, "%Y-%m-%d").date()
        except ValueError:
            return ForecastOut(forecast=[], drop_pct=0.0, alert=0.0)

        current_date = start_date
        forecast_points = []
        forecast_values = []
        day_offset = len(historical_values)

        while current_date <= end_date:
            predicted_value = intercept + slope * day_offset

            if ma_values:
                predicted_value = predicted_value * 0.5 + ma_values[-1] * 0.5

            day_name = current_date.strftime("%A")
            seasonality_factor = seasonality.get(day_name, 1/7)
            predicted_value = predicted_value * (seasonality_factor * 7)

            floor = avg_daily_sales * 0.6
            cap = avg_daily_sales * 1.6 if avg_daily_sales else predicted_value
            predicted_value = min(max(predicted_value, floor), cap)

            forecast_points.append(
                ForecastPoint(date=current_date, expected_amount=round(predicted_value, 2))
            )
            forecast_values.append(predicted_value)

            current_date += timedelta(days=1)
            day_offset += 1

        if forecast_values and avg_daily_sales > 0:
            avg_forecast = sum(forecast_values) / len(forecast_values)
            drop_pct = ((avg_daily_sales - avg_forecast) / avg_daily_sales) * 100
        else:
            drop_pct = 0.0

        alert = anomaly_pct if anomaly_pct > 10 else (abs(drop_pct) if abs(drop_pct) > 20 else 0.0)

        product_forecasts = [
            ProductChannelForecast(
                name=product,
                total=data["total"],
                count=data["count"],
                avg=data["avg"],
                pct=data["pct"]
            )
            for product, data in products_analysis.items()
        ]

        channel_forecasts = [
            ProductChannelForecast(
                name=channel,
                total=data["total"],
                count=data["count"],
                avg=data["avg"],
                pct=data["pct"]
            )
            for channel, data in channels_analysis.items()
        ]

        seasonality_factors = [
            SeasonalityFactor(day=day, factor=round(factor, 3))
            for day, factor in sorted(seasonality.items())
        ]

        meta = ForecastMetadata(
            historical_avg=round(avg_daily_sales, 2),
            std_dev=round(std_dev, 2),
            trend=_trend_label(slope, avg_daily_sales),
            model="trend_seasonal_blend",
            confidence=_confidence_score(std_dev, avg_daily_sales),
        )

        return ForecastOut(
            forecast=forecast_points,
            drop_pct=round(drop_pct, 2),
            alert=round(alert, 2),
            products=product_forecasts,
            channels=channel_forecasts,
            seasonality=seasonality_factors,
            meta=meta,
        )

    finally:
        if owns_session:
            db.close()
