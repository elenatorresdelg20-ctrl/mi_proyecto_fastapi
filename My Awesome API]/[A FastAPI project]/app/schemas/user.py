from pydantic import BaseModel, Field
from typing import Optional


class LoginRequest(BaseModel):
    email: str = Field(..., examples=["user@example.com"])
    password: str = Field(..., examples=["secret"])

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
