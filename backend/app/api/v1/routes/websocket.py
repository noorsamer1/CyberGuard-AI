from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import safe_decode
from app.websocket.manager import ConnectionManager

router = APIRouter()


@router.websocket("/ws")
async def alerts_ws(
    websocket: WebSocket,
    token: str = Query(...),
):
    payload = safe_decode(token)
    if not payload or payload.get("type") != "access":
        await websocket.close(code=4401)
        return
    manager: ConnectionManager = websocket.app.state.ws_manager
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
