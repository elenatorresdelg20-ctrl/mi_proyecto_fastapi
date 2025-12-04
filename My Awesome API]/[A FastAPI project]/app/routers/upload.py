from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import io
import pandas as pd

from app.core.security import get_tenant_context
from app.dependencies import get_db
from app.schemas.dashboard import ColumnInfo, UploadPreviewResponse
from app.schemas.upload import UploadResponse
from app.utils.helpers import normalize_column_names, detect_column_mapping
from app.services.sales import bulk_insert_sales_chunked

router = APIRouter()


@router.post("/api/upload/{tenant_code}", response_model=UploadPreviewResponse)
async def upload_dataset_preview(
    tenant_code: str,
    file: UploadFile = File(...),
    ctx=Depends(get_tenant_context),
):
    """Recibe un archivo y devuelve columnas y muestra de datos para poblar el dashboard."""

    tenant = ctx["tenant"]
    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
    except Exception:
        raise HTTPException(status_code=400, detail="No se pudo leer el archivo subido")

    columns = [ColumnInfo(name=str(col), dtype=str(dtype)) for col, dtype in df.dtypes.items()]
    preview_rows = df.head(20).to_dict(orient="records")

    return UploadPreviewResponse(
        tenant=tenant.code,
        file_name=file.filename or "dataset.csv",
        columns=columns,
        sample_rows=preview_rows,
        total_rows=len(df),
    )


@router.post("/upload_sales/{tenant_code}", response_model=UploadResponse)
async def upload_sales_csv(
    tenant_code: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    ctx=Depends(get_tenant_context),
):
    tenant = ctx["tenant"]

    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
    except Exception:
        raise HTTPException(status_code=400, detail="CSV inválido")

    df = normalize_column_names(df)
    columns = list(df.columns)
    column_map = detect_column_mapping(columns)

    inserted, errors = bulk_insert_sales_chunked(df, tenant.id, db, column_map)
    processed = len(df)
    return UploadResponse(mensaje="Procesado", filas_procesadas=processed, filas_insertadas=inserted, filas_con_error=errors, empresa=tenant.code)
