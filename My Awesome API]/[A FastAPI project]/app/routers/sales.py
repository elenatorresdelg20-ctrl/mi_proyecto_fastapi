from fastapi import APIRouter, UploadFile, File
from app.services.sales_service import process_sales_csv
from app.schemas.sale import SaleOut

router = APIRouter()


@router.post("/upload_sales/{tenant_code}", response_model=SaleOut)
async def upload_sales_csv(tenant_code: str, file: UploadFile = File(...)):
    """Carga un archivo CSV de ventas."""
    result = process_sales_csv(tenant_code, file)
    return result
