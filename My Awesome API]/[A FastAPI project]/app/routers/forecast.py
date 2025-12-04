from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
from app.services.forecast_service import get_forecast_data
from app.schemas.forecast import ForecastOut, ForecastMetadata

router = APIRouter()


@router.get("/forecast/{tenant_code}", response_model=ForecastOut)
def get_forecast(
    tenant_code: str,
    start: str = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    end: str = Query(None, description="Fecha fin (YYYY-MM-DD)")
):
    """
    Obtiene pronóstico de ventas inteligente con análisis detallado.
    
    **Características:**
    - Pronósticos por día basados en tendencia + media móvil
    - Análisis por producto (top 10)
    - Análisis por canal de distribución
    - Factores de seasonalidad (patrón por día de semana)
    - Detección de anomalías y alertas
    
    **Parámetros:**
    - `start`: Fecha inicio (default: hoy)
    - `end`: Fecha fin (default: hoy + 30 días)
    
    **Respuesta incluye:**
    - `forecast`: Lista de pronósticos diarios
    - `drop_pct`: Cambio % vs promedio histórico
    - `alert`: Nivel de alerta por anomalías
    - `products`: Top productos por % de ventas
    - `channels`: Canales con % de contribución
    - `seasonality`: Patrón de ventas por día de semana
    - `meta`: Análisis (tendencia, confianza, modelo usado)
    """
    
    # Usar valores por defecto si no se proporcionan
    if not start:
        start = datetime.now().date().isoformat()
    if not end:
        end = (datetime.now().date() + timedelta(days=30)).isoformat()
    
    try:
        result = get_forecast_data(tenant_code, start, end)
        
        # Calcular metadata adicional si hay pronósticos
        if result.forecast:
            historical_avg = 5000.0  # Placeholder
            std_dev = 800.0  # Placeholder
            
            # Determinar tendencia
            if result.drop_pct < -5:
                trend = "up"
            elif result.drop_pct > 5:
                trend = "down"
            else:
                trend = "stable"
            
            # Calcular confianza basada en alerta
            confidence = max(0.0, 1.0 - (result.alert / 100.0)) if result.alert else 0.9
            
            result.meta = ForecastMetadata(
                historical_avg=historical_avg,
                std_dev=std_dev,
                trend=trend,
                model="hybrid_with_seasonality",
                confidence=round(confidence, 2)
            )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


