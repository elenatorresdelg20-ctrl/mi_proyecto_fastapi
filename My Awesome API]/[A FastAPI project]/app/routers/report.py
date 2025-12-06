from typing import Any, Dict

from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse
from app.services.report_service import (
    generate_calculated_excel_report,
    generate_excel_report,
    generate_pptx_report,
)

router = APIRouter()


@router.post("/report/pptx/{tenant_code}")
async def download_pptx(tenant_code: str, payload: Dict[str, Any] = Body(...)):
    """Descarga un reporte en formato PowerPoint."""
    pptx_bytes = generate_pptx_report(tenant_code, payload)
    return StreamingResponse(
        pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f"attachment; filename=report_{tenant_code}.pptx"}
    )


@router.post("/report/excel/{tenant_code}")
async def download_excel(tenant_code: str, payload: Dict[str, Any] = Body(...)):
    """Descarga un reporte en formato Excel."""
    excel_bytes = generate_excel_report(tenant_code, payload)
    return StreamingResponse(
        excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=report_{tenant_code}.xlsx"}
    )


@router.post("/report/excel/calculado/{tenant_code}")
async def download_calculated_excel(tenant_code: str, payload: Dict[str, Any] = Body(...)):
    """Descarga un Excel con fórmulas calculadas y dashboard enriquecido."""
    excel_bytes = generate_calculated_excel_report(tenant_code, payload)
    return StreamingResponse(
        excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=calculated_{tenant_code}.xlsx"}
    )
