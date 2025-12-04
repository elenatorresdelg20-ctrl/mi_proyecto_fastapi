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
