from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.errors import ApiError
from app.core.security import decode_access_token

router = APIRouter()


class EmployeeWebSocketSessions:
    def __init__(self) -> None:
        self._sessions: dict[int, set[WebSocket]] = {}

    async def register(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._sessions.setdefault(user_id, set()).add(websocket)

    def unregister(self, user_id: int, websocket: WebSocket) -> None:
        sockets = self._sessions.get(user_id)
        if not sockets:
            return
        sockets.discard(websocket)
        if not sockets:
            self._sessions.pop(user_id, None)

    async def send_to_user(self, user_id: int, payload: dict[str, object]) -> None:
        sockets = list(self._sessions.get(user_id, set()))
        for websocket in sockets:
            await websocket.send_json(payload)


employee_ws_sessions = EmployeeWebSocketSessions()


@router.websocket("/ws")
async def employee_ws(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="UNAUTHORIZED")
        return
    try:
        user_id = decode_access_token(token)
    except ApiError:
        await websocket.close(code=4001, reason="UNAUTHORIZED")
        return

    await employee_ws_sessions.register(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        employee_ws_sessions.unregister(user_id, websocket)
