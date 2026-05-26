from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.response import ok, request_id_from
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import CommandRequest
from app.services.default_bot import handle_command

router = APIRouter(prefix="/api/default-bot", tags=["default-bot"])


@router.post("/commands")
def command(
    payload: CommandRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
):
    return ok(handle_command(db, user, payload.command), request_id_from(request))

