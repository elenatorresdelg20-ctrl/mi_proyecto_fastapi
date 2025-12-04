from pydantic import BaseModel
from typing import Dict, Any, List, Optional


class ExplainRequest(BaseModel):
    kpis: Dict[str, float]
    top_changes: Optional[List[Dict[str, Any]]] = None
    anomalies: Optional[List[str]] = None


class ExplainResponse(BaseModel):
    resumen: str
    causa_probable: str
    recomendacion: str
    meta: Dict[str, Any]
