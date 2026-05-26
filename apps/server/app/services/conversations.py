from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.security import create_conversation_id, create_message_id, now_utc, utc_iso
from app.models.bot import Bot, UserBotBinding
from app.models.conversation import Conversation
from app.models.friendship import Friendship
from app.models.message import Message
from app.models.user import User

DEFAULT_BOT_TARGET_ID = "default_bot"


def ensure_conversation(
    db: Session, user: User, target_type: str, target_id: str
) -> tuple[Conversation, bool, list[Message]]:
    _validate_target(db, user, target_type, target_id)
    existing = db.scalar(
        select(Conversation).where(
            Conversation.owner_user_id == user.id,
            Conversation.target_type == target_type,
            Conversation.target_id == target_id,
        )
    )
    if existing:
        return existing, False, []

    conversation = Conversation(
        id=create_conversation_id(),
        conversation_type="direct",
        owner_user_id=user.id,
        target_type=target_type,
        target_id=target_id,
        title=conversation_title(db, target_type, target_id),
    )
    db.add(conversation)
    db.flush()
    initial_messages = _initial_messages(db, conversation)
    if initial_messages:
        update_last_message(conversation, initial_messages[-1])
    db.flush()
    return conversation, True, initial_messages


def ensure_bot_conversation(db: Session, user_id: int, bot_id: str) -> Conversation:
    user = db.get(User, user_id)
    if not user:
        raise ApiError("NOT_FOUND", "用户不存在")
    conversation, _, _ = ensure_conversation(db, user, "openclaw_bot", bot_id)
    return conversation


def list_conversations(db: Session, user_id: int) -> list[Conversation]:
    return list(
        db.scalars(
            select(Conversation)
            .where(Conversation.owner_user_id == user_id)
            .order_by(
                func.coalesce(Conversation.last_message_at, Conversation.updated_at).desc()
            )
        )
    )


def get_owned_conversation(db: Session, user_id: int, conversation_id: str) -> Conversation:
    conversation = db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.owner_user_id == user_id,
        )
    )
    if not conversation:
        raise ApiError("CONVERSATION_NOT_FOUND", "会话不存在")
    return conversation


def conversation_title(db: Session, target_type: str, target_id: str) -> str:
    if target_type == "system_default_bot":
        return "默认 BOT"
    if target_type == "openclaw_bot":
        bot = db.scalar(select(Bot).where(Bot.bot_id == target_id))
        return bot.name if bot else "OpenClaw 员工助手"
    if target_type == "user":
        user = db.get(User, int(target_id))
        return user.real_name if user else target_id
    return target_id


def update_last_message(conversation: Conversation, message: Message) -> None:
    conversation.last_message_id = message.id
    conversation.last_message_at = message.created_at
    conversation.updated_at = now_utc()


def serialize_conversation(db: Session, conversation: Conversation) -> dict[str, object]:
    last_message = db.get(Message, conversation.last_message_id) if conversation.last_message_id else None
    return {
        "id": conversation.id,
        "conversation_type": conversation.conversation_type,
        "target_type": conversation.target_type,
        "target_id": conversation.target_id,
        "title": conversation.title or conversation_title(
            db, conversation.target_type, conversation.target_id
        ),
        "last_message": last_message.content if last_message else None,
        "last_message_id": conversation.last_message_id,
        "last_message_at": utc_iso(conversation.last_message_at),
        "online": _target_online(db, conversation),
    }


def serialize_message(message: Message) -> dict[str, object]:
    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "sender_type": message.sender_type,
        "sender_id": message.sender_id,
        "content_type": message.content_type,
        "content": message.content,
        "status": message.status,
        "created_at": utc_iso(message.created_at),
        "client_message_id": message.client_message_id,
    }


def users_are_friends(db: Session, user_id: int, target_user_id: int) -> bool:
    return (
        db.scalar(
            select(Friendship).where(
                Friendship.status == "accepted",
                or_(
                    (Friendship.requester_id == user_id)
                    & (Friendship.addressee_id == target_user_id),
                    (Friendship.requester_id == target_user_id)
                    & (Friendship.addressee_id == user_id),
                ),
            )
        )
        is not None
    )


def _validate_target(db: Session, user: User, target_type: str, target_id: str) -> None:
    if target_type == "system_default_bot":
        if target_id != DEFAULT_BOT_TARGET_ID:
            raise ApiError("VALIDATION_FAILED", "默认 BOT target_id 必须是 default_bot")
        return
    if target_type == "openclaw_bot":
        bot = db.scalar(select(Bot).where(Bot.bot_id == target_id))
        if not bot:
            raise ApiError("BOT_NOT_FOUND", "BOT 不存在")
        binding = db.scalar(
            select(UserBotBinding).where(
                UserBotBinding.user_id == user.id,
                UserBotBinding.bot_id == target_id,
                UserBotBinding.status == "active",
            )
        )
        if bot.owner_user_id != user.id and not binding:
            raise ApiError("BOT_NOT_OWNED", "BOT 不属于当前员工")
        return
    if target_type == "user":
        try:
            target_user_id = int(target_id)
        except ValueError as exc:
            raise ApiError("VALIDATION_FAILED", "用户 target_id 不合法") from exc
        if target_user_id == user.id:
            raise ApiError("FORBIDDEN", "不能和自己创建会话")
        if not db.get(User, target_user_id):
            raise ApiError("NOT_FOUND", "用户不存在")
        if not users_are_friends(db, user.id, target_user_id):
            raise ApiError("FORBIDDEN", "只有好友之间可以发送消息")
        return
    raise ApiError("VALIDATION_FAILED", "不支持的会话目标类型")


def _initial_messages(db: Session, conversation: Conversation) -> list[Message]:
    if conversation.target_type == "system_default_bot":
        message = Message(
            id=create_message_id(),
            conversation_id=conversation.id,
            sender_type="bot",
            sender_id="system_default_bot",
            content_type="text",
            content="你好！输入 /help 查看可用命令。",
            status="sent",
        )
    elif conversation.target_type == "openclaw_bot":
        message = Message(
            id=create_message_id(),
            conversation_id=conversation.id,
            sender_type="bot",
            sender_id=conversation.target_id,
            content_type="text",
            content="OpenClaw 员工助手已接入。你可以在这里开始对话。",
            status="sent",
        )
    else:
        return []
    db.add(message)
    db.flush()
    return [message]


def _target_online(db: Session, conversation: Conversation) -> bool:
    if conversation.target_type == "system_default_bot":
        return True
    if conversation.target_type == "openclaw_bot":
        bot = db.scalar(select(Bot).where(Bot.bot_id == conversation.target_id))
        return bool(bot and bot.connect_status == "connected")
    if conversation.target_type == "user":
        user = db.get(User, int(conversation.target_id))
        return bool(user and user.online)
    return False
