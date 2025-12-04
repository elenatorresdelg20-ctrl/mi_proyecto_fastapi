from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import io
import pandas as pd

from app.schemas.upload import UploadResponse
from app.core.db import SessionLocal
from app.utils.helpers import normalize_column_names, detect_column_mapping
from app.services.sales import bulk_insert_sales_chunked
from app.models.models import Tenant

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/upload_sales/{tenant_code}", response_model=UploadResponse)
async def upload_sales_csv(tenant_code: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.code == tenant_code).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

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
