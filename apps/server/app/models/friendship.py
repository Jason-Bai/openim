from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.security import now_utc
from app.db.base import Base


class Friendship(Base):
    __tablename__ = "friendships"
    __table_args__ = (
        UniqueConstraint("requester_id", "addressee_id", name="uq_friendships_request_pair"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    requester_id: Mapped[int] = mapped_column(Integer, nullable=False)
    addressee_id: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=now_utc, nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime, default=now_utc, onupdate=now_utc, nullable=False
    )
