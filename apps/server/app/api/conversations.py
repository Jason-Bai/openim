from typing import Annotated, cast

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.response import ok, request_id_from
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import EnsureConversationRequest, SendConversationMessageRequest
from app.services.conversations import (
    ensure_conversation,
    list_conversations,
    serialize_conversation,
    serialize_message,
)
from app.services.messages import list_messages, send_message, serialize_message_page
from app.ws.employee import employee_ws_sessions

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("")
def conversations(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
):
    items = [serialize_conversation(db, conv) for conv in list_conversations(db, user.id)]
    return ok({"items": items}, request_id_from(request))


@router.post("/ensure")
def ensure(
    payload: EnsureConversationRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
):
    conversation, created, initial_messages = ensure_conversation(
        db, user, payload.target_type, payload.target_id
    )
    db.commit()
    return ok(
        {
            "conversation": serialize_conversation(db, conversation),
            "created": created,
            "initial_messages": [serialize_message(message) for message in initial_messages],
        },
        request_id_from(request),
    )


@router.get("/{conversation_id}/messages")
def messages(
    conversation_id: str,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    before: str | None = None,
):
    page = list_messages(db, user, conversation_id, limit=limit, before=before)
    return ok(serialize_message_page(page), request_id_from(request))


@router.post("/{conversation_id}/messages")
async def send(
    conversation_id: str,
    payload: SendConversationMessageRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
):
    result = await send_message(db, user, conversation_id, payload.content, payload.content_type)
    db.commit()
    for event in result.delivery_events:
        await employee_ws_sessions.send_to_user(int(event["user_id"]), cast(dict[str, object], event["payload"]))
    return ok(result.payload, request_id_from(request))
