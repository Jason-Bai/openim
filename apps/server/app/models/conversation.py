from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.security import now_utc
from app.db.base import Base


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        UniqueConstraint(
            "owner_user_id", "target_type", "target_id", name="uq_conversations_owner_target"
        ),
        Index("idx_conversations_owner_sort", "owner_user_id", "last_message_at", "updated_at"),
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    conversation_type: Mapped[str] = mapped_column(String(32), nullable=False)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    last_message_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("messages.id", ondelete="SET NULL", use_alter=True), nullable=True
    )
    last_message_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=now_utc, nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime, default=now_utc, onupdate=now_utc, nullable=False
    )
