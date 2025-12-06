from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional


class IntegrationProvider(str, Enum):
    CRM = "crm"
    ERP = "erp"
    TIKTOK = "tiktok"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"


@dataclass
class IntegrationConfig:
    tenant_code: str
    provider: IntegrationProvider
    base_url: str
    auth_type: str = "bearer"
    api_key: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    extra_headers: Dict[str, str] = field(default_factory=dict)
    is_active: bool = True

    def build_headers(self) -> Dict[str, str]:
        headers = {**self.extra_headers}
        if self.auth_type == "api_key" and self.api_key:
            headers["X-API-Key"] = self.api_key
        elif self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers
