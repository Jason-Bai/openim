from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.errors import ApiError
from app.core.response import ok, request_id_from
from app.core.security import create_access_token, hash_secret, now_utc, utc_iso, verify_secret
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import LoginRequest, RegisterRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


def user_data(user: User) -> dict[str, object]:
    return {
        "id": user.id,
        "username": user.username,
        "employee_id": user.employee_id,
        "real_name": user.real_name,
        "online": user.online,
        "last_seen_at": utc_iso(user.last_seen_at),
    }


@router.post("/register")
def register(payload: RegisterRequest, request: Request, db: Annotated[Session, Depends(get_db)]):
    if db.scalar(select(User).where(User.username == payload.username)):
        raise ApiError("VALIDATION_FAILED", "用户名已存在")
    if db.scalar(select(User).where(User.employee_id == payload.employee_id)):
        raise ApiError("VALIDATION_FAILED", "员工工号已存在")
    user = User(
        username=payload.username,
        password_hash=hash_secret(payload.password),
        employee_id=payload.employee_id,
        real_name=payload.real_name,
    )
    db.add(user)
    db.commit()
    return ok({"user": user_data(user)}, request_id_from(request))


@router.post("/login")
def login(payload: LoginRequest, request: Request, db: Annotated[Session, Depends(get_db)]):
    user = db.scalar(select(User).where(User.username == payload.username))
    if not user or not verify_secret(payload.password, user.password_hash):
        raise ApiError("AUTH_FAILED", "用户名或密码错误")
    user.online = True
    user.last_seen_at = now_utc()
    db.commit()
    return ok(
        {"access_token": create_access_token(user.id), "token_type": "Bearer", "user": user_data(user)},
        request_id_from(request),
    )


@router.get("/me")
def me(user: Annotated[User, Depends(current_user)], request: Request):
    return ok({"user": user_data(user)}, request_id_from(request))
