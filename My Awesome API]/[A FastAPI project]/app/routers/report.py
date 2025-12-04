from fastapi import APIRouter, Body, Depends
from fastapi.responses import StreamingResponse

from app.core.security import get_tenant_context
from app.schemas.dashboard import KpiCard, ReportDashboardResponse, ReportTableRow
from app.schemas.kpis import KPIs
from app.services.report_service import generate_pptx_report, generate_excel_report

router = APIRouter()


@router.get("/api/report/{tenant_code}", response_model=ReportDashboardResponse)
async def report_dashboard(tenant_code: str, ctx=Depends(get_tenant_context)):
    """Entrega métricas agregadas que consumen las tablas y cards del dashboard de reportes."""

    tenant = ctx["tenant"]
    highlights = [
        KpiCard(label="Ingresos", value=250000.0, change=6.4),
        KpiCard(label="Clientes", value=1800, change=2.3),
        KpiCard(label="Churn", value=3.1, change=-0.5),
    ]
    table = [
        ReportTableRow(segment="Retail", revenue=125000, growth=5.4, share=0.5),
        ReportTableRow(segment="Online", revenue=95000, growth=7.1, share=0.38),
        ReportTableRow(segment="Wholesale", revenue=30000, growth=-1.2, share=0.12),
    ]
    return ReportDashboardResponse(tenant=tenant.code, highlights=highlights, table=table)


@router.post("/report/pptx/{tenant_code}")
async def download_pptx(tenant_code: str, payload: KPIs = Body(...), ctx=Depends(get_tenant_context)):
    """Descarga un reporte en formato PowerPoint."""
    tenant = ctx["tenant"]
    pptx_bytes = generate_pptx_report(tenant.code, payload)
    return StreamingResponse(
        pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f"attachment; filename=report_{tenant.code}.pptx"}
    )


@router.post("/report/excel/{tenant_code}")
async def download_excel(tenant_code: str, payload: KPIs = Body(...), ctx=Depends(get_tenant_context)):
    """Descarga un reporte en formato Excel."""
    tenant = ctx["tenant"]
    excel_bytes = generate_excel_report(tenant.code, payload)
    return StreamingResponse(
        excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=report_{tenant.code}.xlsx"}
    )
