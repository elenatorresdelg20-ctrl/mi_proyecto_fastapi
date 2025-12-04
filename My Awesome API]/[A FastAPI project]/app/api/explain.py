from fastapi import APIRouter
from app.services.ai_service import get_explanation
from app.schemas.kpis import KPIs

router = APIRouter()

@router.post("/explain/{tenant_code}")
async def explain_data(tenant_code: str, payload: KPIs):
    return await get_explanation(tenant_code, payload)
