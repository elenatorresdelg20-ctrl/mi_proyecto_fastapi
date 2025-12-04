from pydantic import BaseModel
from datetime import datetime

class SaleIn(BaseModel):
    date: datetime
    product: str
    amount: float
    channel: str

class SaleOut(SaleIn):
    id: int
    tenant_id: int

    class Config:
        orm_mode = True
