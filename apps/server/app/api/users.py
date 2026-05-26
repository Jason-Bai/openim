from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.response import ok, request_id_from
from app.core.security import utc_iso
from app.db.session import get_db
from app.models.friendship import Friendship
from app.models.user import User

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("")
def list_users(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(current_user)],
):
    users = list(db.scalars(select(User).order_by(User.id.asc())))
    relationships = relationship_map(db, current.id)
    return ok(
        {
            "items": [
                {
                    "id": user.id,
                    "username": user.username,
                    "employee_id": user.employee_id,
                    "real_name": user.real_name,
                    "contact_type": "user",
                    "relationship": "self" if user.id == current.id else relationships.get(user.id, "none"),
                    "online": True if user.id == current.id else user.online,
                    "last_seen_at": utc_iso(user.last_seen_at),
                }
                for user in users
            ]
        },
        request_id_from(request),
    )


def relationship_map(db: Session, user_id: int) -> dict[int, str]:
    rows = db.scalars(
        select(Friendship).where(
            (Friendship.requester_id == user_id) | (Friendship.addressee_id == user_id)
        )
    )
    result: dict[int, str] = {}
    for row in rows:
        if row.requester_id == user_id:
            other_id = row.addressee_id
            result[other_id] = "friend" if row.status == "accepted" else "pending_out"
        else:
            other_id = row.requester_id
            result[other_id] = "friend" if row.status == "accepted" else "pending_in"
    return result
