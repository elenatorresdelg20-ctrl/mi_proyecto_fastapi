from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Tuple

import requests

from app.core.settings import INTEGRATION_MAX_RETRIES, INTEGRATION_TIMEOUT
from app.schemas.integration import IntegrationConfig, IntegrationProvider

logger = logging.getLogger("saas_app.integrations")


class IntegrationRepository:
    """Simple repository for external integrations.

    Tries to read from the database when available; otherwise falls back to in-memory seed.
    """

    def __init__(self, seed: Optional[Dict[Tuple[str, IntegrationProvider], IntegrationConfig]] = None):
        self._store: Dict[Tuple[str, IntegrationProvider], IntegrationConfig] = seed or {}

    def upsert(self, config: IntegrationConfig) -> None:
        self._store[(config.tenant_code, config.provider)] = config

    def get(self, tenant_code: str, provider: IntegrationProvider, db: Any | None = None) -> Optional[IntegrationConfig]:
        # DB lookup is optional to keep the service usable without SQLAlchemy installed
        if db is not None:
            try:
                from app.models.models import ExternalIntegration, Tenant
            except Exception:
                logger.debug("DB integrations unavailable; using in-memory store")
            else:
                tenant = db.query(Tenant).filter(Tenant.code == tenant_code).first()
                if tenant:
                    record = (
                        db.query(ExternalIntegration)
                        .filter(ExternalIntegration.tenant_id == tenant.id, ExternalIntegration.provider == provider.value)
                        .first()
                    )
                    if record and record.is_active:
                        return IntegrationConfig(
                            tenant_code=tenant_code,
                            provider=provider,
                            base_url=record.extra_config or "",
                            auth_type=record.auth_type,
                            api_key=record.api_key,
                            access_token=record.access_token,
                            refresh_token=record.refresh_token,
                            expires_at=record.token_expires_at,
                            is_active=record.is_active,
                        )
        return self._store.get((tenant_code, provider))


DEFAULT_INTEGRATIONS: Dict[Tuple[str, IntegrationProvider], IntegrationConfig] = {
    (
        "default",
        IntegrationProvider.CRM,
    ): IntegrationConfig(
        tenant_code="default",
        provider=IntegrationProvider.CRM,
        base_url="https://crm.example.internal/api",
        auth_type="api_key",
        api_key="crm-dev-token",
        extra_headers={"Accept": "application/json"},
    ),
    (
        "default",
        IntegrationProvider.ERP,
    ): IntegrationConfig(
        tenant_code="default",
        provider=IntegrationProvider.ERP,
        base_url="https://erp.example.internal/api",
        auth_type="bearer",
        access_token="erp-dev-token",
        extra_headers={"Accept": "application/json"},
    ),
    (
        "default",
        IntegrationProvider.TIKTOK,
    ): IntegrationConfig(
        tenant_code="default",
        provider=IntegrationProvider.TIKTOK,
        base_url="https://business-api.tiktok.com",
        auth_type="bearer",
        access_token="tiktok-dev-token",
    ),
    (
        "default",
        IntegrationProvider.FACEBOOK,
    ): IntegrationConfig(
        tenant_code="default",
        provider=IntegrationProvider.FACEBOOK,
        base_url="https://graph.facebook.com",
        auth_type="bearer",
        access_token="facebook-dev-token",
    ),
    (
        "default",
        IntegrationProvider.INSTAGRAM,
    ): IntegrationConfig(
        tenant_code="default",
        provider=IntegrationProvider.INSTAGRAM,
        base_url="https://graph.instagram.com",
        auth_type="bearer",
        access_token="instagram-dev-token",
    ),
}


class IntegrationService:
    def __init__(
        self,
        repo: IntegrationRepository | None = None,
        timeout: float = INTEGRATION_TIMEOUT,
        max_retries: int = INTEGRATION_MAX_RETRIES,
        http_client: Callable[..., requests.Session] | None = None,
    ):
        self.repo = repo or IntegrationRepository(seed=DEFAULT_INTEGRATIONS)
        self.timeout = timeout
        self.max_retries = max_retries
        self.http_client_factory = http_client or requests.Session

    def _resolve_config(self, tenant_code: str, provider: IntegrationProvider, db: Any | None = None) -> IntegrationConfig:
        config = self.repo.get(tenant_code, provider, db=db)
        if not config or not config.is_active:
            raise ValueError(f"Integración no encontrada o inactiva para tenant={tenant_code}, provider={provider.value}")
        return config

    def _request(
        self,
        method: str,
        config: IntegrationConfig,
        path: str,
        *,
        params: Dict[str, Any] | None = None,
        json_body: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        attempt = 0
        headers = config.build_headers()
        last_error: Exception | None = None
        while attempt <= self.max_retries:
            attempt += 1
            try:
                with self.http_client_factory() as client:
                    url = f"{config.base_url}{path}"
                    response = client.request(method=method, url=url, headers=headers, params=params, json=json_body, timeout=self.timeout)
                    response.raise_for_status()
                    logger.info(
                        "Integration call ok provider=%s tenant=%s status=%s",
                        config.provider.value,
                        config.tenant_code,
                        response.status_code,
                    )
                    return response.json() if response.content else {}
            except Exception as exc:  # pragma: no cover - covered via retries
                last_error = exc
                logger.warning(
                    "Integration call failed provider=%s tenant=%s attempt=%s error=%s",
                    config.provider.value,
                    config.tenant_code,
                    attempt,
                    exc,
                )
                if attempt > self.max_retries:
                    break
                time.sleep(0.05 * attempt)
        raise RuntimeError(f"No se pudo completar la integración con {config.provider.value}: {last_error}")

    def fetch_json(
        self,
        tenant_code: str,
        provider: IntegrationProvider,
        path: str,
        *,
        params: Dict[str, Any] | None = None,
        payload: Dict[str, Any] | None = None,
        db: Any | None = None,
    ) -> Dict[str, Any]:
        config = self._resolve_config(tenant_code, provider, db=db)
        return self._request("GET", config, path, params=params, json_body=payload)

    def push_json(
        self,
        tenant_code: str,
        provider: IntegrationProvider,
        path: str,
        payload: Dict[str, Any],
        *,
        db: Any | None = None,
    ) -> Dict[str, Any]:
        config = self._resolve_config(tenant_code, provider, db=db)
        return self._request("POST", config, path, json_body=payload)

    def connection_summary(self, tenant_code: str, db: Any | None = None) -> Dict[str, Any]:
        summary: Dict[str, Any] = {}
        for provider in IntegrationProvider:
            try:
                config = self._resolve_config(tenant_code, provider, db=db)
            except ValueError:
                continue
            summary[provider.value] = {
                "base_url": config.base_url,
                "auth_type": config.auth_type,
                "has_token": bool(config.api_key or config.access_token),
                "is_active": config.is_active,
                "expires_at": config.expires_at.isoformat() if isinstance(config.expires_at, datetime) else None,
            }
        return summary

    def export_config(self, tenant_code: str) -> str:
        relevant = {
            provider.value: asdict(cfg)
            for (t_code, provider), cfg in self.repo._store.items()
            if t_code == tenant_code
        }
        return json.dumps(relevant, default=str)


integration_service = IntegrationService()
