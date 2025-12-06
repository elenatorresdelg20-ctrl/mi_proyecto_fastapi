from fastapi import APIRouter, Depends, UploadFile, File

from app.dependencies.tenant import verify_tenant_api_key
from app.services.sales_service import process_sales_csv
from app.schemas.sale import SaleOut

router = APIRouter()


@router.post("/upload_sales/{tenant_code}", response_model=SaleOut)
async def upload_sales_csv(tenant_code: str, file: UploadFile = File(...), tenant=Depends(verify_tenant_api_key)):
    """Carga un archivo CSV de ventas."""
    result = process_sales_csv(tenant_code, file)
    return result
