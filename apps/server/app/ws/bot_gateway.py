import asyncio
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ApiError
from app.db.session import SessionLocal
from app.models.bot import Bot
from app.services.bot_gateway_sessions import bot_gateway_sessions
from app.services.bots import (
    authenticate_bot,
    log_connection,
    mark_handshake,
    mark_heartbeat,
    serialize_bot_for_owner,
)
from app.ws.employee import employee_ws_sessions

router = APIRouter()


@router.websocket("/bot-gateway/ws")
async def bot_gateway(websocket: WebSocket) -> None:
    await websocket.accept()
    db = SessionLocal()
    bot: Bot | None = None
    try:
        auth_message = await asyncio.wait_for(
            websocket.receive_json(), timeout=settings.auth_timeout_seconds
        )
        if auth_message.get("type") != "auth":
            await _send_error(websocket, auth_message, "AUTH_FAILED", "首条消息必须是 auth")
            await websocket.close(code=4000, reason="AUTH_FAILED")
            return

        bot = authenticate_bot(db, str(auth_message.get("bot_id")), str(auth_message.get("token")))
        log_connection(db, bot_id=bot.bot_id, event_type="auth", request_id=auth_message.get("request_id"))
        db.commit()
        await websocket.send_json(
            {
                "type": "auth.result",
                "request_id": auth_message.get("request_id"),
                "protocol_version": auth_message.get("protocol_version", "bot-v1"),
                "ok": True,
                "bot_id": bot.bot_id,
            }
        )

        while True:
            message = await websocket.receive_json()
            message_type = message.get("type")
            if message_type == "handshake":
                mark_handshake(db, bot, str(message.get("protocol_version", "bot-v1")))
                log_connection(
                    db,
                    bot_id=bot.bot_id,
                    event_type="handshake",
                    request_id=message.get("request_id"),
                )
                db.commit()
                bot_gateway_sessions.register(bot.bot_id, websocket)
                await employee_ws_sessions.send_to_user(
                    bot.owner_user_id,
                    {
                        "type": "bot.status_changed",
                        "bot": _status_event_bot(db, bot),
                    },
                )
                await websocket.send_json(
                    {
                        "type": "handshake.result",
                        "request_id": message.get("request_id"),
                        "protocol_version": message.get("protocol_version", "bot-v1"),
                        "ok": True,
                        "bot_id": bot.bot_id,
                    }
                )
                continue

            if message_type == "heartbeat":
                mark_heartbeat(db, bot)
                db.commit()
                await websocket.send_json(
                    {
                        "type": "heartbeat.result",
                        "request_id": message.get("request_id"),
                        "protocol_version": message.get("protocol_version", "bot-v1"),
                        "ok": True,
                        "bot_id": bot.bot_id,
                    }
                )
                continue

            if message_type == "send_message":
                content = message.get("content")
                if not isinstance(content, dict):
                    await _send_error(websocket, message, "MESSAGE_FORMAT_INVALID", "content 格式错误")
                    continue
                bot_gateway_sessions.resolve_reply(bot.bot_id, str(message.get("request_id")), message)
                await websocket.send_json(
                    {
                        "type": "send_message.result",
                        "request_id": message.get("request_id"),
                        "protocol_version": message.get("protocol_version", "bot-v1"),
                        "ok": True,
                    }
                )
                continue

            await _send_error(websocket, message, "MESSAGE_FORMAT_INVALID", "不支持的消息类型")
    except TimeoutError:
        await websocket.close(code=4000, reason="AUTH_TIMEOUT")
    except ApiError as exc:
        if websocket.client_state.name != "DISCONNECTED":
            await websocket.send_json(
                {
                    "type": "auth.result",
                    "request_id": None,
                    "protocol_version": "bot-v1",
                    "ok": False,
                    "error": {
                        "code": exc.code,
                        "message": exc.message,
                        "retryable": exc.retryable,
                    },
                }
            )
            await websocket.close(code=4000, reason=exc.code)
    except WebSocketDisconnect:
        pass
    finally:
        if bot is not None:
            bot_gateway_sessions.unregister(bot.bot_id, websocket)
            bot.connect_status = "disconnected"
            db.commit()
            try:
                await employee_ws_sessions.send_to_user(
                    bot.owner_user_id,
                    {
                        "type": "bot.status_changed",
                        "bot": _status_event_bot(db, bot),
                    },
                )
            except Exception:
                pass
        db.close()


async def _send_error(websocket: WebSocket, message: dict[str, Any], code: str, text: str) -> None:
    await websocket.send_json(
        {
            "type": f"{message.get('type', 'unknown')}.result",
            "request_id": message.get("request_id"),
            "protocol_version": message.get("protocol_version", "bot-v1"),
            "ok": False,
            "error": {"code": code, "message": text, "retryable": False},
        }
    )


def _status_event_bot(db: Session, bot: Bot) -> dict[str, object]:
    serialized = serialize_bot_for_owner(db, bot)
    return {
        "bot_id": serialized["bot_id"],
        "connect_status": serialized["connect_status"],
        "binding_status": serialized["binding_status"],
    }
