from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse
from app.services.report_service import generate_pptx_report, generate_excel_report
from app.schemas.kpis import KPIs

router = APIRouter()

@router.post("/report/pptx/{tenant_code}")
async def download_pptx(tenant_code: str, payload: KPIs = Body(...)):
    pptx_bytes = generate_pptx_report(tenant_code, payload)
    return StreamingResponse(pptx_bytes, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation")

@router.post("/report/excel/{tenant_code}")
async def download_excel(tenant_code: str, payload: KPIs = Body(...)):
    excel_bytes = generate_excel_report(tenant_code, payload)
    return StreamingResponse(excel_bytes, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
