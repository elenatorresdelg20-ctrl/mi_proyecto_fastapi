from pydantic import BaseModel
from typing import Dict, Any


class UploadResponse(BaseModel):
    mensaje: str
    filas_procesadas: int
    filas_insertadas: int
    filas_con_error: int
    empresa: str
