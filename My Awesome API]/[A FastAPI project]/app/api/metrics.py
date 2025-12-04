from fastapi import APIRouter, WebSocket
from app.utils.cache import cache_get

router = APIRouter()

@router.websocket("/ws/metrics/{tenant_code}")
async def ws_metrics(websocket: WebSocket, tenant_code: str):
    await websocket.accept()
    data = cache_get(tenant_code)
    if data:
        await websocket.send_json({"type": "metrics", "payload": data})
    try:
        while True:
            msg = await websocket.receive_text()
            await websocket.send_text(f"Recibido: {msg}")
    except Exception:
        await websocket.close()
