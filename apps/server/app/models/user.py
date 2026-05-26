from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.security import now_utc
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    employee_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    real_name: Mapped[str] = mapped_column(String(128), nullable=False)
    online: Mapped[bool] = mapped_column(default=False, nullable=False)
    last_seen_at: Mapped[DateTime] = mapped_column(DateTime, default=now_utc, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=now_utc, nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime, default=now_utc, onupdate=now_utc, nullable=False
    )

    bots = relationship("Bot", back_populates="owner")
