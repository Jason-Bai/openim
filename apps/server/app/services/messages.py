from dataclasses import dataclass

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.security import create_client_message_id, create_message_id, now_utc
from app.models.message import Message
from app.models.user import User
from app.services.bot_gateway_sessions import bot_gateway_sessions
from app.services.conversations import (
    ensure_conversation,
    get_owned_conversation,
    serialize_conversation,
    serialize_message,
    update_last_message,
    users_are_friends,
)
from app.services.default_bot import handle_command


@dataclass
class MessagePage:
    items: list[Message]
    has_more: bool
    next_before: str | None


@dataclass
class SendMessageResult:
    payload: dict[str, object]
    delivery_events: list[dict[str, object]]


def list_messages(
    db: Session,
    user: User,
    conversation_id: str,
    *,
    limit: int = 50,
    before: str | None = None,
) -> MessagePage:
    conversation = get_owned_conversation(db, user.id, conversation_id)
    capped_limit = min(max(limit, 1), 100)
    filters = [Message.conversation_id == conversation.id]
    if before:
        cursor = db.get(Message, before)
        if not cursor or cursor.conversation_id != conversation.id:
            raise ApiError("VALIDATION_FAILED", "消息游标不合法")
        filters.append(
            or_(
                Message.created_at < cursor.created_at,
                and_(Message.created_at == cursor.created_at, Message.id < cursor.id),
            )
        )

    rows = list(
        db.scalars(
            select(Message)
            .where(*filters)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(capped_limit + 1)
        )
    )
    has_more = len(rows) > capped_limit
    page_items = rows[:capped_limit]
    display_items = list(reversed(page_items))
    return MessagePage(
        items=display_items,
        has_more=has_more,
        next_before=display_items[0].id if has_more and display_items else None,
    )


def serialize_message_page(page: MessagePage) -> dict[str, object]:
    return {
        "items": [serialize_message(message) for message in page.items],
        "has_more": page.has_more,
        "next_before": page.next_before,
    }


async def send_message(
    db: Session,
    user: User,
    conversation_id: str,
    content: str,
    content_type: str,
) -> SendMessageResult:
    conversation = get_owned_conversation(db, user.id, conversation_id)
    normalized_content = _validate_content(content, content_type)
    delivery_events: list[dict[str, object]] = []
    if conversation.target_type == "system_default_bot":
        messages = _send_default_bot(db, user, conversation, normalized_content)
    elif conversation.target_type == "openclaw_bot":
        messages = await _send_openclaw_bot(db, user, conversation, normalized_content)
    elif conversation.target_type == "user":
        messages, delivery_events = _send_user(db, user, conversation, normalized_content)
    else:
        raise ApiError("MESSAGE_DELIVERY_FAILED", "该会话类型暂不支持发送")

    return SendMessageResult(
        payload={
            "conversation": serialize_conversation(db, conversation),
            "messages": [serialize_message(message) for message in messages],
        },
        delivery_events=delivery_events,
    )


def _validate_content(content: str, content_type: str) -> str:
    if content_type not in {"text", "code"}:
        raise ApiError("VALIDATION_FAILED", "不支持的消息类型")
    normalized = content.strip()
    if not normalized:
        raise ApiError("VALIDATION_FAILED", "消息不能为空")
    if len(normalized) > 4000:
        raise ApiError("VALIDATION_FAILED", "消息不能超过 4000 字")
    return normalized


def _persist_message(
    db: Session,
    *,
    conversation_id: str,
    sender_type: str,
    sender_id: str,
    content_type: str,
    content: str,
    client_message_id: str | None = None,
    created_at=None,
) -> Message:
    message = Message(
        id=create_message_id(),
        conversation_id=conversation_id,
        client_message_id=client_message_id,
        sender_type=sender_type,
        sender_id=sender_id,
        content_type=content_type,
        content=content,
        status="sent",
        created_at=created_at or now_utc(),
    )
    db.add(message)
    db.flush()
    return message


def _send_default_bot(
    db: Session, user: User, conversation, content: str
) -> list[Message]:
    user_message = _persist_message(
        db,
        conversation_id=conversation.id,
        sender_type="user",
        sender_id=str(user.id),
        content_type="text",
        content=content,
    )
    reply = handle_command(db, user, content)
    bot_message = _persist_message(
        db,
        conversation_id=conversation.id,
        sender_type="bot",
        sender_id="system_default_bot",
        content_type=reply["reply_type"],
        content=reply["content"],
    )
    update_last_message(conversation, bot_message)
    return [user_message, bot_message]


def _send_user(
    db: Session, user: User, conversation, content: str
) -> tuple[list[Message], list[dict[str, object]]]:
    target_user_id = int(conversation.target_id)
    target_user = db.get(User, target_user_id)
    if not target_user:
        raise ApiError("NOT_FOUND", "用户不存在")
    if not users_are_friends(db, user.id, target_user_id):
        raise ApiError("FORBIDDEN", "只有好友之间可以发送消息")

    receiver_conversation, _, _ = ensure_conversation(
        db, target_user, "user", str(user.id)
    )
    client_message_id = create_client_message_id()
    created_at = now_utc()
    sender_message = _persist_message(
        db,
        conversation_id=conversation.id,
        sender_type="user",
        sender_id=str(user.id),
        content_type="text",
        content=content,
        client_message_id=client_message_id,
        created_at=created_at,
    )
    receiver_message = _persist_message(
        db,
        conversation_id=receiver_conversation.id,
        sender_type="user",
        sender_id=str(user.id),
        content_type="text",
        content=content,
        client_message_id=client_message_id,
        created_at=created_at,
    )
    update_last_message(conversation, sender_message)
    update_last_message(receiver_conversation, receiver_message)
    return [sender_message], [
        {
            "user_id": target_user_id,
            "payload": {"type": "message.new", "message": serialize_message(receiver_message)},
        },
        {
            "user_id": target_user_id,
            "payload": {
                "type": "conversation.updated",
                "conversation": serialize_conversation(db, receiver_conversation),
            },
        },
    ]


async def _send_openclaw_bot(
    db: Session, user: User, conversation, content: str
) -> list[Message]:
    user_message = _persist_message(
        db,
        conversation_id=conversation.id,
        sender_type="user",
        sender_id=str(user.id),
        content_type="text",
        content=content,
    )
    db.commit()
    try:
        reply = await bot_gateway_sessions.request_reply(
            bot_id=conversation.target_id,
            conversation_id=conversation.id,
            user_id=user.id,
            text=content,
        )
    except ApiError:
        system_message = _persist_message(
            db,
            conversation_id=conversation.id,
            sender_type="system",
            sender_id="system",
            content_type="text",
            content="OpenClaw 员工助手暂时没有返回，请稍后重试。",
        )
        update_last_message(conversation, system_message)
        return [user_message, system_message]

    reply_content = reply.get("content") if isinstance(reply, dict) else None
    text = reply_content.get("text") if isinstance(reply_content, dict) else ""
    bot_message = _persist_message(
        db,
        conversation_id=conversation.id,
        sender_type="bot",
        sender_id=conversation.target_id,
        content_type="text",
        content=text or "OpenClaw 没有返回文本内容",
    )
    update_last_message(conversation, bot_message)
    return [user_message, bot_message]
