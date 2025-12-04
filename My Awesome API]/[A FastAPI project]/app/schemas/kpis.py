from pydantic import BaseModel

class KPIs(BaseModel):
    ventas: float
    transacciones: int
    ticket_promedio: float
    margen: float
