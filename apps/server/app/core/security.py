import base64
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import base58
import bcrypt
import jwt
import ulid

from app.core.config import settings
from app.core.errors import ApiError


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def utc_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def hash_secret(value: str) -> str:
    return bcrypt.hashpw(value.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_secret(value: str, hashed: str) -> bool:
    return bcrypt.checkpw(value.encode("utf-8"), hashed.encode("utf-8"))


def create_bot_id() -> str:
    return f"bot_{ulid.new()}"


def create_conversation_id() -> str:
    return f"conv_{ulid.new()}"


def create_message_id() -> str:
    return f"msg_{ulid.new()}"


def create_client_message_id() -> str:
    return f"cmsg_{ulid.new()}"


def create_token() -> str:
    return f"ocb_live_{base58.b58encode(secrets.token_bytes(32)).decode('ascii')}"


def token_last4(token: str) -> str:
    return token[-4:] if len(token) >= 4 else ""


def mask_token(last4: str | None) -> str:
    return f"ocb_live_****_{last4}" if last4 else "[MASKED]"


def _jwt_expiry() -> datetime:
    value = settings.jwt_expires_in
    if value.endswith("d"):
        return datetime.now(timezone.utc) + timedelta(days=int(value[:-1]))
    if value.endswith("h"):
        return datetime.now(timezone.utc) + timedelta(hours=int(value[:-1]))
    return datetime.now(timezone.utc) + timedelta(seconds=int(value))


def create_access_token(user_id: int) -> str:
    payload: dict[str, Any] = {"sub": str(user_id), "exp": _jwt_expiry()}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> int:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return int(payload["sub"])
    except Exception as exc:
        raise ApiError("UNAUTHORIZED", "登录已过期或无效") from exc


def generate_trace_id() -> str:
    return "trace_" + base64.urlsafe_b64encode(secrets.token_bytes(12)).decode("ascii").rstrip("=")
