import logging
from datetime import datetime
from typing import Dict, Optional, Union

from fastapi import Depends, HTTPException, Request, Security, WebSocket
from fastapi.security import APIKeyHeader
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.models import Tenant as TenantModel
from app.schemas.tenant import Tenant

api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)
logger = logging.getLogger("saas_app.tenants")


class TenantRepository:
    """Repository to resolve tenants from DB or an in-memory store."""

    def __init__(self, seed: Optional[Dict[str, Tenant]] = None):
        self._tenants: Dict[str, Tenant | TenantModel] = seed or {}

    def add(self, tenant: Tenant) -> None:
        self._tenants[tenant.tenant_code] = tenant

    def prime_from_db(self, db: Session) -> int:
        """Load active tenants from the database into the in-memory cache."""
        try:
            tenants = db.query(TenantModel).filter(TenantModel.is_active.is_(True)).all()
        except SQLAlchemyError as exc:
            logger.warning("No se pudo sincronizar tenants desde DB: %s", exc)
            return 0

        for tenant in tenants:
            self._tenants[tenant.code] = tenant
        return len(tenants)

    def get_tenant(self, tenant_code: str, db: Session | None = None):
        if db is not None:
            try:
                tenant_obj = db.query(TenantModel).filter(TenantModel.code == tenant_code).first()
                if tenant_obj:
                    return tenant_obj
            except SQLAlchemyError as exc:
                logger.warning("Error consultando tenant %s en DB: %s", tenant_code, exc)

        return self._tenants.get(tenant_code)


tenant_seed = Tenant(
    tenant_code="default",
    name="Default Tenant",
    api_key="dev-key",
    is_active=True,
    created_at=datetime.utcnow(),
)
TENANT_REPOSITORY = TenantRepository(seed={tenant_seed.tenant_code: tenant_seed})


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Connection = Union[Request, WebSocket]


def resolve_tenant(
    tenant_code: str,
    request: Connection,
    db: Session = Depends(get_db),
    repo: TenantRepository = TENANT_REPOSITORY,
):
    tenant = repo.get_tenant(tenant_code, db=db)
    if tenant is None or getattr(tenant, "is_active", False) is False:
        raise HTTPException(status_code=404, detail="Tenant no encontrado o inactivo")

    request.state.tenant_code = tenant_code
    request.state.tenant_id = getattr(tenant, "id", None)
    return tenant


def verify_tenant_api_key(
    tenant_code: str,
    request: Connection,
    api_key: Optional[str] = Security(api_key_scheme),
    tenant=Depends(resolve_tenant),
):
    expected = getattr(tenant, "api_key", None)
    if not api_key:
        raise HTTPException(status_code=401, detail="API key requerida")
    if expected != api_key:
        raise HTTPException(status_code=403, detail="API key inválida para el tenant")

    request.state.tenant = tenant
    return tenant
