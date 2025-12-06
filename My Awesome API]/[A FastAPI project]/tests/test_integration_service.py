from app.schemas.integration import IntegrationConfig, IntegrationProvider
from app.services.integration_service import IntegrationRepository, IntegrationService


class FakeResponse:
    def __init__(self, status_code: int = 200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.content = b"{}" if payload is not None else b""

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"status {self.status_code}")

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responder):
        self._responder = responder

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def request(self, method, url, headers=None, params=None, json=None, timeout=None):
        return self._responder(method, url, headers or {}, params or {}, json or {}, timeout)


def test_build_headers_supports_api_key_and_bearer():
    config_api = IntegrationConfig(
        tenant_code="t1",
        provider=IntegrationProvider.CRM,
        base_url="https://crm.test",
        auth_type="api_key",
        api_key="crm-token",
    )
    config_bearer = IntegrationConfig(
        tenant_code="t1",
        provider=IntegrationProvider.ERP,
        base_url="https://erp.test",
        access_token="bearer-token",
    )

    assert config_api.build_headers()["X-API-Key"] == "crm-token"
    assert config_bearer.build_headers()["Authorization"] == "Bearer bearer-token"


def test_fetch_json_uses_fake_session_and_returns_payload():
    captured = {}

    def responder(method, url, headers, params, json, timeout):
        captured["method"] = method
        captured["url"] = url
        captured["headers"] = headers
        captured["params"] = params
        captured["json"] = json
        return FakeResponse(payload={"ok": True, "provider": "crm"})

    repo = IntegrationRepository(
        seed={
            (
                "tenant-x",
                IntegrationProvider.CRM,
            ): IntegrationConfig(
                tenant_code="tenant-x",
                provider=IntegrationProvider.CRM,
                base_url="https://crm.example",
                auth_type="api_key",
                api_key="secret",
            )
        }
    )
    service = IntegrationService(repo=repo, http_client=lambda: FakeSession(responder))

    payload = service.fetch_json("tenant-x", IntegrationProvider.CRM, "/customers", params={"limit": 10})

    assert payload == {"ok": True, "provider": "crm"}
    assert captured["url"] == "https://crm.example/customers"
    assert captured["headers"]["X-API-Key"] == "secret"
    assert captured["params"] == {"limit": 10}


def test_connection_summary_includes_active_providers():
    repo = IntegrationRepository(
        seed={
            (
                "t-summary",
                IntegrationProvider.ERP,
            ): IntegrationConfig(
                tenant_code="t-summary",
                provider=IntegrationProvider.ERP,
                base_url="https://erp.example",
                access_token="erp-token",
            ),
            (
                "t-summary",
                IntegrationProvider.TIKTOK,
            ): IntegrationConfig(
                tenant_code="t-summary",
                provider=IntegrationProvider.TIKTOK,
                base_url="https://tiktok.example",
                access_token="tik-token",
                is_active=False,
            ),
        }
    )
    service = IntegrationService(repo=repo, http_client=lambda: FakeSession(lambda *args, **kwargs: FakeResponse()))

    summary = service.connection_summary("t-summary")

    assert "erp" in summary
    assert summary["erp"]["has_token"] is True
    assert "tiktok" not in summary  # inactive integration is omitted
