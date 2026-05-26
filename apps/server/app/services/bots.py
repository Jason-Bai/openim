import json

from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ApiError
from app.core.security import (
    create_bot_id,
    create_token,
    hash_secret,
    mask_token,
    now_utc,
    token_last4,
    utc_iso,
    verify_secret,
)
from app.models.bot import Bot, BotConnectionLog, UserBotBinding
from app.db.session import SessionLocal


def get_owned_bot(db: Session, user_id: int, bot_id: str) -> Bot:
    bot = db.scalar(select(Bot).where(Bot.bot_id == bot_id))
    if not bot:
        raise ApiError("BOT_NOT_FOUND", "BOT 不存在")
    if bot.owner_user_id != user_id:
        raise ApiError("BOT_NOT_OWNED", "BOT 不属于当前员工")
    if bot.connect_status == "revoked":
        raise ApiError("BOT_REVOKED", "BOT 已撤销")
    return bot


def create_bot_slot(db: Session, user_id: int, name: str | None = None) -> Bot:
    token = create_token()
    bot = Bot(
        bot_id=create_bot_id(),
        owner_user_id=user_id,
        name=name or "OpenClaw 员工助手",
        bot_type="openclaw_assistant",
        token_hash=hash_secret(token),
        token_last4=token_last4(token),
        connect_status="pending",
    )
    db.add(bot)
    db.flush()
    return bot


def list_user_bots(db: Session, user_id: int) -> list[dict[str, object]]:
    bots = db.scalars(select(Bot).where(Bot.owner_user_id == user_id).order_by(Bot.created_at.asc()))
    return [serialize_bot_for_owner(db, bot) for bot in bots]


def serialize_bot_for_owner(db: Session, bot: Bot) -> dict[str, object]:
    binding = db.scalar(
        select(UserBotBinding).where(
            UserBotBinding.user_id == bot.owner_user_id,
            UserBotBinding.bot_id == bot.bot_id,
            UserBotBinding.status == "active",
        )
    )
    return {
        "bot_id": bot.bot_id,
        "name": bot.name,
        "bot_type": bot.bot_type,
        "connect_status": bot.connect_status,
        "binding_status": binding.status if binding else "none",
        "last_seen_at": utc_iso(bot.last_seen_at),
        "first_connected_at": utc_iso(bot.first_connected_at),
    }


def diagnose_bot(db: Session, user_id: int, bot_id: str) -> dict[str, object]:
    bot = get_owned_bot(db, user_id, bot_id)
    binding = db.scalar(
        select(UserBotBinding).where(
            UserBotBinding.user_id == user_id,
            UserBotBinding.bot_id == bot.bot_id,
            UserBotBinding.status == "active",
        )
    )
    latest_log = db.scalar(
        select(BotConnectionLog)
        .where(BotConnectionLog.bot_id == bot.bot_id)
        .order_by(BotConnectionLog.created_at.desc(), BotConnectionLog.id.desc())
        .limit(1)
    )
    return {
        "bot_id": bot.bot_id,
        "name": bot.name,
        "connect_status": bot.connect_status,
        "binding_status": binding.status if binding else "none",
        "last_seen_at": utc_iso(bot.last_seen_at),
        "last_event_type": latest_log.event_type if latest_log else None,
        "last_error_code": latest_log.error_code if latest_log else None,
        "token_status": "revealed_once" if bot.token_revealed_at else "not_revealed",
    }


def reset_runtime_bot_connections() -> None:
    with SessionLocal() as db:
        db.execute(
            update(Bot)
            .where(Bot.connect_status.in_(["connected", "authenticating"]))
            .values(connect_status="disconnected", updated_at=now_utc())
        )
        db.commit()


def connect_info(db: Session, user_id: int, bot_id: str) -> tuple[dict[str, object], bool]:
    bot = get_owned_bot(db, user_id, bot_id)
    if bot.token_revealed_at is None:
        token = create_token()
        bot.token_hash = hash_secret(token)
        bot.token_last4 = token_last4(token)
        bot.token_revealed_at = now_utc()
        bot.updated_at = now_utc()
        return (
            _connect_info_payload(bot_id=bot.bot_id, token=token, token_status="revealed_once"),
            False,
        )
    return (
        _connect_info_payload(
            bot_id=bot.bot_id,
            token=mask_token(bot.token_last4),
            token_status="masked",
        ),
        True,
    )


def regenerate_connect_info(db: Session, user_id: int, bot_id: str) -> dict[str, object]:
    bot = get_owned_bot(db, user_id, bot_id)
    token = create_token()
    bot.token_hash = hash_secret(token)
    bot.token_last4 = token_last4(token)
    bot.token_revealed_at = now_utc()
    bot.token_regenerated_at = now_utc()
    bot.updated_at = now_utc()
    return _connect_info_payload(bot_id=bot.bot_id, token=token, token_status="revealed_once")


def _connect_info_payload(bot_id: str, token: str, token_status: str) -> dict[str, object]:
    return {
        "bot_id": bot_id,
        "token": token,
        "token_status": token_status,
        "gateway_url": settings.bot_gateway_public_url,
        "protocol_version": "bot-v1",
        "plugin": {
            "type": "npm",
            "package": "@openim/openclaw-bot-plugin",
            "version": settings.plugin_version,
            "install": settings.plugin_install_command,
            "docs": "docs/plugin-npm-package.md",
        },
    }


def disconnect_bot(db: Session, user_id: int, bot_id: str) -> Bot:
    bot = get_owned_bot(db, user_id, bot_id)
    bot.connect_status = "disconnected"
    bot.updated_at = now_utc()
    return bot


def delete_bot(db: Session, user_id: int, bot_id: str) -> None:
    bot = get_owned_bot(db, user_id, bot_id)
    if bot.connect_status in {"connected", "authenticating"}:
        raise ApiError("VALIDATION_FAILED", "请先断开 BOT 后再删除")
    db.delete(bot)


def authenticate_bot(db: Session, bot_id: str, token: str) -> Bot:
    bot = db.scalar(select(Bot).where(Bot.bot_id == bot_id))
    if not bot or not verify_secret(token, bot.token_hash):
        raise ApiError("AUTH_FAILED", "bot_id 或 token 错误")
    if bot.connect_status == "revoked":
        raise ApiError("BOT_REVOKED", "BOT 已撤销")
    if bot.connect_status == "connected":
        raise ApiError("BOT_ALREADY_CONNECTED", "同一个 bot_id 已存在活跃连接")
    bot.connect_status = "authenticating"
    bot.updated_at = now_utc()
    return bot


def mark_handshake(db: Session, bot: Bot, protocol_version: str) -> None:
    now = now_utc()
    bot.protocol_version = protocol_version
    bot.connect_status = "connected"
    bot.first_connected_at = bot.first_connected_at or now
    bot.last_seen_at = now
    bot.updated_at = now
    binding = db.scalar(
        select(UserBotBinding).where(
            UserBotBinding.user_id == bot.owner_user_id,
            UserBotBinding.bot_id == bot.bot_id,
        )
    )
    if not binding:
        db.add(
            UserBotBinding(
                user_id=bot.owner_user_id,
                bot_id=bot.bot_id,
                binding_type=bot.bot_type,
                status="active",
            )
        )
    else:
        binding.status = "active"
        binding.revoked_at = None


def mark_heartbeat(db: Session, bot: Bot) -> None:
    bot.last_seen_at = now_utc()
    bot.updated_at = now_utc()


def log_connection(
    db: Session,
    *,
    bot_id: str,
    event_type: str,
    request_id: str | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
    remote_addr: str | None = None,
) -> None:
    db.add(
        BotConnectionLog(
            bot_id=bot_id,
            event_type=event_type,
            request_id=request_id,
            error_code=error_code,
            error_message=error_message,
            remote_addr=remote_addr,
        )
    )


def json_block(payload: dict[str, object]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)
