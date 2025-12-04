from fastapi import APIRouter
from app.services.forecast_service import get_forecast_data
from app.schemas.forecast import ForecastOut

router = APIRouter()

@router.get("/forecast/{tenant_code}", response_model=ForecastOut)
def get_forecast(tenant_code: str, start: str, end: str):
    data = get_forecast_data(tenant_code, start, end)
    return data
