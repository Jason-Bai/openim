from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.errors import ApiError
from app.core.response import ok, request_id_from
from app.db.session import get_db
from app.models.friendship import Friendship
from app.models.user import User

router = APIRouter(prefix="/api/friends", tags=["friends"])


@router.post("/{user_id}")
def create_friend_request(
    user_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(current_user)],
):
    if user_id == current.id:
        raise ApiError("VALIDATION_FAILED", "不能添加自己为好友")
    target = db.get(User, user_id)
    if not target:
        raise ApiError("NOT_FOUND", "用户不存在")

    existing = db.scalar(
        select(Friendship).where(
            ((Friendship.requester_id == current.id) & (Friendship.addressee_id == user_id))
            | ((Friendship.requester_id == user_id) & (Friendship.addressee_id == current.id))
        )
    )
    if existing:
        relationship = relationship_for(current.id, existing)
        return ok({"relationship": relationship}, request_id_from(request))

    friendship = Friendship(requester_id=current.id, addressee_id=user_id, status="pending")
    db.add(friendship)
    db.commit()
    return ok({"relationship": "pending_out"}, request_id_from(request))


@router.post("/{user_id}/accept")
def accept_friend_request(
    user_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(current_user)],
):
    friendship = incoming_pending_friendship(user_id, db, current)
    friendship.status = "accepted"
    db.commit()
    return ok({"relationship": "friend"}, request_id_from(request))


def relationship_for(current_user_id: int, friendship: Friendship) -> str:
    if friendship.status == "accepted":
        return "friend"
    if friendship.requester_id == current_user_id:
        return "pending_out"
    return "pending_in"


def incoming_pending_friendship(user_id: int, db: Session, current: User) -> Friendship:
    if user_id == current.id:
        raise ApiError("VALIDATION_FAILED", "不能处理自己的好友申请")
    target = db.get(User, user_id)
    if not target:
        raise ApiError("NOT_FOUND", "用户不存在")
    friendship = db.scalar(
        select(Friendship).where(
            Friendship.requester_id == user_id,
            Friendship.addressee_id == current.id,
            Friendship.status == "pending",
        )
    )
    if not friendship:
        raise ApiError("NOT_FOUND", "好友申请不存在")
    return friendship
