from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.response import ok, request_id_from
from app.db.session import get_db
from app.models.user import User
from app.services.bot_gateway_sessions import bot_gateway_sessions
from app.services.bots import get_owned_bot
from app.services.conversations import ensure_bot_conversation

router = APIRouter(prefix="/api/bots", tags=["bot-messages"])


class BotMessageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


@router.post("/{bot_id}/messages")
async def send_bot_message(
    bot_id: str,
    payload: BotMessageRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
):
    bot = get_owned_bot(db, user.id, bot_id)
    conversation = ensure_bot_conversation(db, user.id, bot.bot_id)
    db.commit()
    reply = await bot_gateway_sessions.request_reply(
        bot_id=bot.bot_id,
        conversation_id=conversation.id,
        user_id=user.id,
        text=payload.text,
    )
    content = reply.get("content") if isinstance(reply, dict) else None
    text = content.get("text") if isinstance(content, dict) else ""
    return ok(
        {
            "bot_id": bot.bot_id,
            "conversation_id": conversation.id,
            "reply": {
                "content": text,
                "request_id": reply.get("request_id"),
            },
        },
        request_id_from(request),
    )
