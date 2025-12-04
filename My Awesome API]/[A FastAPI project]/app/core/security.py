from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.config import get_settings
from app.core.rate_limiter import require_rate_allowed
from app.dependencies import get_db
from app.models.tenant import Tenant
from app.models.user import User

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def authenticate_user(db: Session, identifier: str, password: str) -> User:
    """Valida usuario por username o email y verifica contraseña."""

    user = (
        db.query(User)
        .filter(or_(User.username == identifier, User.email == identifier))
        .first()
    )
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")
    return user


def _build_token_payload(user: User, tenant_code: str) -> Dict[str, Any]:
    now = datetime.now(tz=timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    return {
        "sub": str(user.id),
        "tenant_id": user.tenant_id,
        "tenant_code": tenant_code,
        "is_admin": user.is_tenant_admin,
        "iat": int(now.timestamp()),
        "exp": expire,
    }


def create_access_token(user: User, tenant_code: str) -> str:
    payload = _build_token_payload(user, tenant_code)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def _decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido") from exc


def _get_user_from_token(db: Session, token: str) -> User:
    payload = _decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token sin subject")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")
    return user


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    return _get_user_from_token(db, token)


def get_tenant_context(
    tenant_code: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    tenant: Optional[Tenant] = db.query(Tenant).filter(Tenant.code == tenant_code).first()
    if not tenant or not tenant.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado o inactivo")

    if current_user.tenant_id != tenant.id and not current_user.is_tenant_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado para este tenant")

    client_ip = request.client.host if request.client else "unknown"
    remaining, reset = require_rate_allowed(tenant_code, client_ip)
    request.state.rate_limit = {"remaining": remaining, "reset": reset}

    return {"tenant": tenant, "user": current_user, "rate_limit": {"remaining": remaining, "reset": reset}}
