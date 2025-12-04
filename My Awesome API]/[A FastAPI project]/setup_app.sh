#!/bin/bash

# Crear estructura de directorios
mkdir -p app/api app/services app/models app/schemas app/core app/utils

# Asegurar que sean paquetes de Python
touch app/__init__.py
touch app/api/__init__.py
touch app/services/__init__.py
touch app/models/__init__.py
touch app/schemas/__init__.py
touch app/core/__init__.py
touch app/utils/__init__.py

# -------------------------------------------------------------------
# app/models/tenant.py
cat <<EOF > app/models/tenant.py
from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    logo_url = Column(String, nullable=True)
    primary_color = Column(String, nullable=True)
EOF

# -------------------------------------------------------------------
# app/models/user.py
cat <<EOF > app/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    is_tenant_admin = Column(Boolean, default=False)
EOF

# -------------------------------------------------------------------
# app/models/sale.py
cat <<EOF > app/models/sale.py
from sqlalchemy import Column, Integer, Float, DateTime, String, Index
from app.core.database import Base

class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (Index("idx_tenant_date", "tenant_id", "date"),)
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True)
    date = Column(DateTime, index=True)
    product = Column(String)
    amount = Column(Float)
    channel = Column(String, default="Upload")
    cost = Column(Float, nullable=True)
EOF

# -------------------------------------------------------------------
# app/schemas/user.py
cat <<EOF > app/schemas/user.py
from pydantic import BaseModel
from typing import Optional

class UserOut(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    tenant_id: int
    is_active: bool
    is_tenant_admin: bool

    class Config:
        orm_mode = True
EOF

# -------------------------------------------------------------------
# app/schemas/sale.py
cat <<EOF > app/schemas/sale.py
from pydantic import BaseModel
from datetime import datetime

class SaleIn(BaseModel):
    date: datetime
    product: str
    amount: float
    channel: str

class SaleOut(SaleIn):
    id: int
    tenant_id: int

    class Config:
        orm_mode = True
EOF

# -------------------------------------------------------------------
# app/schemas/tenant.py
cat <<EOF > app/schemas/tenant.py
from pydantic import BaseModel

class TenantOut(BaseModel):
    id: int
    name: str
    code: str
    is_active: bool

    class Config:
        orm_mode = True
EOF

# -------------------------------------------------------------------
# app/schemas/forecast.py
cat <<EOF > app/schemas/forecast.py
from pydantic import BaseModel
from datetime import date
from typing import List

class ForecastPoint(BaseModel):
    date: date
    expected_amount: float

class ForecastOut(BaseModel):
    forecast: List[ForecastPoint]
    drop_pct: float
    alert: float
EOF

# -------------------------------------------------------------------
# app/schemas/kpis.py
cat <<EOF > app/schemas/kpis.py
from pydantic import BaseModel

class KPIs(BaseModel):
    ventas: float
    transacciones: int
    ticket_promedio: float
    margen: float
EOF

# -------------------------------------------------------------------
# app/api/sales.py
cat <<EOF > app/api/sales.py
from fastapi import APIRouter, UploadFile, File
from app.services.sales_service import process_sales_csv
from app.schemas.sale import SaleOut

router = APIRouter()

@router.post("/upload_sales/{tenant_code}", response_model=SaleOut)
async def upload_sales_csv(tenant_code: str, file: UploadFile = File(...)):
    result = process_sales_csv(tenant_code, file)
    return result
EOF

# -------------------------------------------------------------------
# app/api/forecast.py
cat <<EOF > app/api/forecast.py
from fastapi import APIRouter
from app.services.forecast_service import get_forecast_data
from app.schemas.forecast import ForecastOut

router = APIRouter()

@router.get("/forecast/{tenant_code}", response_model=ForecastOut)
def get_forecast(tenant_code: str, start: str, end: str):
    data = get_forecast_data(tenant_code, start, end)
    return data
EOF

# -------------------------------------------------------------------
# app/api/report.py
cat <<EOF > app/api/report.py
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
EOF

# -------------------------------------------------------------------
# app/api/auth.py
cat <<EOF > app/api/auth.py
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.user import UserOut
from app.core.security import authenticate_user, create_access_token, get_current_user

router = APIRouter()

@router.post("/auth/token", response_model=dict)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}

@router.get("/auth/me", response_model=UserOut)
def read_users_me(current_user = Depends(get_current_user)):
    return current_user
EOF

# -------------------------------------------------------------------
# app/api/explain.py
cat <<EOF > app/api/explain.py
from fastapi import APIRouter
from app.services.ai_service import get_explanation
from app.schemas.kpis import KPIs

router = APIRouter()

@router.post("/explain/{tenant_code}")
async def explain_data(tenant_code: str, payload: KPIs):
    return await get_explanation(tenant_code, payload)
EOF

# -------------------------------------------------------------------
# app/api/metrics.py
cat <<EOF > app/api/metrics.py
from fastapi import APIRouter, WebSocket
from app.utils.cache import cache_get

router = APIRouter()

@router.websocket("/ws/metrics/{tenant_code}")
async def ws_metrics(websocket: WebSocket, tenant_code: str):
    await websocket.accept()
    data = cache_get(tenant_code)
    if data:
        await websocket.send_json({"type": "metrics", "payload": data})
    try:
        while True:
            msg = await websocket.receive_text()
            await websocket.send_text(f"Recibido: {msg}")
    except Exception:
        await websocket.close()
EOF

# -------------------------------------------------------------------
# app/services/sales_service.py
cat <<EOF > app/services/sales_service.py
import pandas as pd
from io import StringIO

def process_sales_csv(tenant_code: str, file):
    content = file.file.read().decode("utf-8")
    df = pd.read_csv(StringIO(content))
    total = len(df)
    first = df.iloc[0]
    return {
        "id": total,
        "tenant_id": 1,
        "date": first["date"],
        "product": first["product"],
        "amount": first["amount"],
        "channel": first.get("channel", "Upload"),
    }
EOF

# -------------------------------------------------------------------
# app/services/forecast_service.py
cat <<EOF > app/services/forecast_service.py
def get_forecast_data(tenant_code: str, start: str, end: str):
    return {"forecast": [], "drop_pct": 0.0, "alert": 0.0}
EOF

# -------------------------------------------------------------------
# app/services/report_service.py
cat <<EOF > app/services/report_service.py
from io import BytesIO

def generate_pptx_report(tenant_code: str, payload):
    return BytesIO(b"Dummy PPTX content")

def generate_excel_report(tenant_code: str, payload):
    return BytesIO(b"Dummy Excel content")
EOF

# -------------------------------------------------------------------
# app/services/ai_service.py
cat <<EOF > app/services/ai_service.py
async def get_explanation(tenant_code: str, payload):
    return {"resumen": "Ejemplo", "causa_probable": "Ejemplo", "recomendacion": "Ejemplo"}
EOF

# -------------------------------------------------------------------
# app/core/config.py
cat <<EOF > app/core/config.py
import os

SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
EOF

# -------------------------------------------------------------------
# app/core/database.py
cat <<EOF > app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
EOF

# -------------------------------------------------------------------
# app/core/security.py
cat <<EOF > app/core/security.py
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str):
    return User(
        id=1,
        username=username,
        full_name="",
        email="",
        hashed_password=get_password_hash(password),
        tenant_id=1,
        is_active=True,
        is_tenant_admin=False,
    )

def create_access_token(user_id: int):
    to_encode = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user():
    return {
        "id": 1,
        "username": "demo",
        "full_name": "Demo User",
        "email": "demo@example.com",
        "tenant_id": 1,
        "is_active": True,
        "is_tenant_admin": False,
    }
EOF

# -------------------------------------------------------------------
# app/core/loggi
