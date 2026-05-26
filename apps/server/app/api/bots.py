from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.response import ok, request_id_from
from app.db.session import get_db
from app.models.user import User
from app.services.bots import (
    connect_info,
    create_bot_slot,
    delete_bot,
    disconnect_bot,
    list_user_bots,
    regenerate_connect_info,
)

router = APIRouter(prefix="/api/bots", tags=["bots"])


@router.get("")
def list_bots(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
):
    return ok({"items": list_user_bots(db, user.id)}, request_id_from(request))


@router.post("")
def create_bot(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
):
    bot = create_bot_slot(db, user.id)
    db.commit()
    return ok(
        {
            "bot": {
                "bot_id": bot.bot_id,
                "name": bot.name,
                "bot_type": bot.bot_type,
                "connect_status": bot.connect_status,
            }
        },
        request_id_from(request),
    )


@router.get("/{bot_id}/connect-info")
def get_connect_info(
    bot_id: str,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
):
    data, _ = connect_info(db, user.id, bot_id)
    db.commit()
    return ok(data, request_id_from(request))


@router.post("/{bot_id}/connect-info/regenerate")
def regenerate(
    bot_id: str,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
):
    data = regenerate_connect_info(db, user.id, bot_id)
    db.commit()
    return ok(data, request_id_from(request))


@router.post("/{bot_id}/disconnect")
def disconnect(
    bot_id: str,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
):
    bot = disconnect_bot(db, user.id, bot_id)
    db.commit()
    return ok({"bot_id": bot.bot_id, "connect_status": bot.connect_status}, request_id_from(request))


@router.delete("/{bot_id}")
def remove_bot(
    bot_id: str,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
):
    delete_bot(db, user.id, bot_id)
    db.commit()
    return ok({"bot_id": bot_id, "deleted": True}, request_id_from(request))

