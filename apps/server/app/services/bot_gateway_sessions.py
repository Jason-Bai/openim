import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket

from app.core.errors import ApiError


@dataclass
class BotGatewaySession:
    bot_id: str
    websocket: WebSocket
    pending: dict[str, asyncio.Future[dict[str, Any]]] = field(default_factory=dict)


class BotGatewaySessionRegistry:
    def __init__(self) -> None:
        self._sessions: dict[str, BotGatewaySession] = {}

    def register(self, bot_id: str, websocket: WebSocket) -> None:
        self._sessions[bot_id] = BotGatewaySession(bot_id=bot_id, websocket=websocket)

    def unregister(self, bot_id: str, websocket: WebSocket) -> bool:
        current = self._sessions.get(bot_id)
        if current and current.websocket is websocket:
            for future in current.pending.values():
                if not future.done():
                    future.set_exception(ApiError("BOT_STATUS_SYNC_FAILED", "BOT 已断开连接"))
            self._sessions.pop(bot_id, None)
            return True
        return False

    async def request_reply(
        self,
        *,
        bot_id: str,
        conversation_id: str,
        user_id: int,
        text: str,
        timeout_seconds: int = 60,
    ) -> dict[str, Any]:
        session = self._sessions.get(bot_id)
        if not session:
            raise ApiError("BOT_STATUS_SYNC_FAILED", "BOT 当前不在线")

        request_id = f"msg_{uuid.uuid4().hex}"
        message_id = f"umsg_{uuid.uuid4().hex}"
        future: asyncio.Future[dict[str, Any]] = asyncio.get_running_loop().create_future()
        session.pending[request_id] = future
        await session.websocket.send_json(
            {
                "type": "inbound_message",
                "request_id": request_id,
                "protocol_version": "bot-v1",
                "conversation_id": conversation_id,
                "message_id": message_id,
                "from": {"type": "user", "id": str(user_id)},
                "content": {"type": "text", "text": text},
                "created_at": "now",
            }
        )
        try:
            return await asyncio.wait_for(future, timeout=timeout_seconds)
        except TimeoutError as exc:
            raise ApiError("MESSAGE_SEND_FAILED", "等待 BOT 回复超时", retryable=True) from exc
        finally:
            session.pending.pop(request_id, None)

    def resolve_reply(self, bot_id: str, request_id: str, payload: dict[str, Any]) -> bool:
        session = self._sessions.get(bot_id)
        if not session:
            return False
        future = session.pending.get(request_id)
        if not future or future.done():
            return False
        future.set_result(payload)
        return True


bot_gateway_sessions = BotGatewaySessionRegistry()
