from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.security import now_utc
from app.db.base import Base


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index("idx_messages_conversation_created", "conversation_id", "created_at", "id"),
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    client_message_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    sender_type: Mapped[str] = mapped_column(String(16), nullable=False)
    sender_id: Mapped[str] = mapped_column(String(64), nullable=False)
    content_type: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="sent")
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=now_utc, nullable=False)
