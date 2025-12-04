from pydantic import BaseModel

class TenantOut(BaseModel):
    id: int
    name: str
    code: str
    is_active: bool

    class Config:
        orm_mode = True
