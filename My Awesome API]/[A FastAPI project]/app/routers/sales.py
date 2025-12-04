from fastapi import APIRouter, Depends, File, UploadFile

from app.core.security import get_tenant_context
from app.schemas.dashboard import BreakdownRow, SalesDashboardResponse, SalesFunnelStage
from app.schemas.sale import SaleOut
from app.services.sales_service import process_sales_csv

router = APIRouter()


@router.post("/sales/upload/{tenant_code}", response_model=SaleOut)
async def upload_sales_csv(tenant_code: str, file: UploadFile = File(...), ctx=Depends(get_tenant_context)):
    """Carga un archivo CSV de ventas."""
    result = process_sales_csv(tenant_code, file)
    return result


@router.get("/api/sales/{tenant_code}", response_model=SalesDashboardResponse)
async def sales_dashboard(tenant_code: str, ctx=Depends(get_tenant_context)):
    """Datos mockeados para el dashboard de ventas en Next.js."""

    tenant = ctx["tenant"]
    funnel = [
        SalesFunnelStage(stage="Prospectos", value=1200, conversion=0.0),
        SalesFunnelStage(stage="Oportunidades", value=480, conversion=40.0),
        SalesFunnelStage(stage="Ganadas", value=240, conversion=50.0),
    ]
    top_products = [
        BreakdownRow(name="Suite Analytics", value=72000, change=6.1),
        BreakdownRow(name="CX Cloud", value=54000, change=4.8),
        BreakdownRow(name="Smart POS", value=31000, change=3.0),
    ]
    return SalesDashboardResponse(tenant=tenant.code, funnel=funnel, top_products=top_products)
