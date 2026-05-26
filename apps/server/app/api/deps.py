from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User


def current_user(
    db: Annotated[Session, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise ApiError("UNAUTHORIZED", "请先登录")
    user_id = decode_access_token(authorization.removeprefix("Bearer ").strip())
    user = db.get(User, user_id)
    if not user:
        raise ApiError("UNAUTHORIZED", "用户不存在")
    return user

