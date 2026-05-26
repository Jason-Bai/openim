from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.api.users import relationship_map
from app.core.response import ok, request_id_from
from app.core.security import utc_iso
from app.db.session import get_db
from app.models.user import User
from app.services.bots import list_user_bots

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


@router.get("")
def list_contacts(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(current_user)],
):
    user_contacts = _user_contacts(db, current)
    ai_contacts = [_default_bot_contact(), *[_bot_contact(bot) for bot in list_user_bots(db, current.id)]]
    return ok({"ai": ai_contacts, "all": [*ai_contacts, *user_contacts]}, request_id_from(request))


def _user_contacts(db: Session, current: User) -> list[dict[str, object]]:
    users = list(db.scalars(select(User).order_by(User.id.asc())))
    relationships = relationship_map(db, current.id)
    return [
        {
            "id": str(user.id),
            "contact_type": "user",
            "title": user.real_name,
            "subtitle": user.username if user.online or user.id == current.id else "离线",
            "online": True if user.id == current.id else user.online,
            "user": {
                "id": user.id,
                "username": user.username,
                "employee_id": user.employee_id,
                "real_name": user.real_name,
                "contact_type": "user",
                "relationship": "self" if user.id == current.id else relationships.get(user.id, "none"),
                "online": True if user.id == current.id else user.online,
                "last_seen_at": utc_iso(user.last_seen_at),
            },
        }
        for user in users
    ]


def _default_bot_contact() -> dict[str, object]:
    return {
        "id": "default_bot",
        "contact_type": "system_default_bot",
        "title": "默认 BOT",
        "subtitle": "系统助手",
        "online": True,
    }


def _bot_contact(bot: dict[str, object]) -> dict[str, object]:
    return {
        "id": bot["bot_id"],
        "contact_type": "openclaw_bot",
        "title": bot["name"],
        "subtitle": bot["bot_id"],
        "online": bot["connect_status"] == "connected",
        "bot": bot,
    }
