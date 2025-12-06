from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Tenant(BaseModel):
    tenant_code: str = Field(alias="code")
    name: str
    api_key: str
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
