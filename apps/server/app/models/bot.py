from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.security import now_utc
from app.db.base import Base


class Bot(Base):
    __tablename__ = "bots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bot_id: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    bot_type: Mapped[str] = mapped_column(String(32), nullable=False, default="openclaw_assistant")
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    token_last4: Mapped[str] = mapped_column(String(4), nullable=False)
    token_revealed_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
    token_regenerated_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
    connect_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    protocol_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    first_connected_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
    last_seen_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=now_utc, nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime, default=now_utc, onupdate=now_utc, nullable=False
    )
    revoked_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)

    owner = relationship("User", back_populates="bots")


class UserBotBinding(Base):
    __tablename__ = "user_bot_bindings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    bot_id: Mapped[str] = mapped_column(String(40), nullable=False)
    binding_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=now_utc, nullable=False)
    revoked_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)


class BotConnectionLog(Base):
    __tablename__ = "bot_connection_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bot_id: Mapped[str] = mapped_column(String(40), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    remote_addr: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=now_utc, nullable=False)

