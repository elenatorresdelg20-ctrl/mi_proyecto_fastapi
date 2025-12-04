from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import authenticate_user, create_access_token, get_current_user
from app.dependencies import get_db
from app.models.tenant import Tenant
from app.schemas.user import LoginRequest, UserOut

router = APIRouter()

@router.post("/auth/token", response_model=dict)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, form_data.username, form_data.password)
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if not tenant or not tenant.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant inactivo")

    token = create_access_token(user, tenant.code)
    return {"access_token": token, "token_type": "bearer", "tenant": tenant.code}


@router.post("/auth/login", response_model=dict)
def login_json(payload: LoginRequest, db: Session = Depends(get_db)):
    """Login vía JSON para clientes web (Next.js)."""

    user = authenticate_user(db, payload.email, payload.password)
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if not tenant or not tenant.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant inactivo")

    token = create_access_token(user, tenant.code)
    return {
        "access_token": token,
        "token_type": "bearer",
        "tenant": tenant.code,
        "user": {"id": user.id, "username": user.username, "email": user.email},
    }

@router.get("/auth/me", response_model=UserOut)
def read_users_me(current_user=Depends(get_current_user)):
    return current_user
