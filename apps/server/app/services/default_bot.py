from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.security import now_utc
from app.models.user import User
from app.services.bots import (
    connect_info,
    create_bot_slot,
    delete_bot,
    diagnose_bot,
    disconnect_bot,
    json_block,
    list_user_bots,
    regenerate_connect_info,
)
from app.services.pending_actions import pending_actions


HELP_TEXT = """你好！我是你的默认助手 BOT
支持命令：
/help                 查看帮助
/my-bots              查看你创建的 BOT
/new-bot              创建 OpenClaw 员工助手接入槽位
/delete-bot {bot_id}  删除 BOT
/connect {bot_id}     获取连接信息
/disconnect {bot_id}  断开 BOT
/diagnose {bot_id}    诊断 BOT 连接状态
"""


def handle_command(db: Session, user: User, command: str) -> dict[str, str]:
    command = command.strip()
    if not command:
        return text_reply("请输入 /help 查看可用命令")

    pending = _handle_pending_if_any(db, user, command)
    if pending:
        return pending

    parts = command.split()
    name = parts[0]

    if name == "/help":
        return text_reply(HELP_TEXT)
    if name == "/new-bot":
        bot = create_bot_slot(db, user.id)
        db.commit()
        return text_reply(
            f"已创建 OpenClaw 员工助手接入槽位。\nBOT_ID: {bot.bot_id}\n下一步输入：/connect {bot.bot_id}"
        )
    if name == "/my-bots":
        return text_reply(_format_bots(list_user_bots(db, user.id)))
    if name == "/connect":
        if len(parts) < 2:
            return text_reply(_select_bot_prompt(db, user.id, "/connect {bot_id}"))
        bot_id = parts[1]
        data, masked = connect_info(db, user.id, bot_id)
        if masked:
            confirm_text = f"confirm regenerate {bot_id}"
            expires_at = now_utc() + timedelta(minutes=5)
            pending_actions.set(
                user.id,
                bot_id,
                {
                    "action": "regenerate_token",
                    "user_id": user.id,
                    "bot_id": bot_id,
                    "confirm_text": confirm_text,
                    "created_at": now_utc().isoformat(),
                    "expires_at": expires_at.isoformat(),
                },
            )
            db.commit()
            return text_reply(
                "当前 token 已展示过，不能再次查看明文。\n"
                f"masked token: {data['token']}\n"
                f"如需重新生成 token，请在 5 分钟内输入：{confirm_text}\n"
                "取消请输入：cancel"
            )
        db.commit()
        return code_reply(json_block(data))
    if name == "/disconnect":
        if len(parts) < 2:
            return text_reply(_select_bot_prompt(db, user.id, "/disconnect {bot_id}"))
        bot = disconnect_bot(db, user.id, parts[1])
        db.commit()
        return text_reply(f"BOT {bot.bot_id} 已断开连接")
    if name == "/diagnose":
        if len(parts) < 2:
            return text_reply("请输入要诊断的 BOT ID：/diagnose {bot_id}")
        return text_reply(_format_diagnosis(diagnose_bot(db, user.id, parts[1])))
    if name == "/delete-bot":
        if len(parts) < 2:
            return text_reply("请输入要删除的 BOT ID：/delete-bot {bot_id}")
        delete_bot(db, user.id, parts[1])
        db.commit()
        return text_reply(f"BOT {parts[1]} 已删除")

    return text_reply("未知命令。请输入 /help 查看可用命令")


def _handle_pending_if_any(db: Session, user: User, command: str) -> dict[str, str] | None:
    parts = command.split()
    if command == "cancel":
        for bot in list_user_bots(db, user.id):
            pending_actions.delete(user.id, str(bot["bot_id"]))
        return text_reply("已取消本次操作")
    if len(parts) == 3 and parts[0] == "confirm" and parts[1] == "regenerate":
        bot_id = parts[2]
        pending = pending_actions.get(user.id, bot_id)
        if not pending:
            return text_reply(f"确认已过期，请重新输入：/connect {bot_id}")
        if pending["confirm_text"] != command:
            return text_reply(f"确认文本不正确，请输入：{pending['confirm_text']}")
        data = regenerate_connect_info(db, user.id, bot_id)
        pending_actions.delete(user.id, bot_id)
        db.commit()
        return code_reply(json_block(data))
    if command.startswith("confirm"):
        return text_reply("确认文本不正确，请按默认 BOT 提示完整输入确认文本")
    return None


def _format_bots(items: list[dict[str, object]]) -> str:
    if not items:
        return "你的 BOT 列表为空。输入 /new-bot 创建 OpenClaw 员工助手接入槽位。"
    lines = ["你的 BOT 列表："]
    for item in items:
        lines.append(
            "ID: {bot_id} | 名称: {name} | 类型: {bot_type} | 连接: {connect_status} | 绑定: {binding_status}".format(
                **item
            )
        )
    return "\n".join(lines)


def _format_diagnosis(data: dict[str, object]) -> str:
    return "\n".join(
        [
            f"BOT_ID: {data['bot_id']}",
            f"名称: {data['name']}",
            f"连接状态: {data['connect_status']}",
            f"绑定状态: {data['binding_status']}",
            f"最后在线: {data['last_seen_at'] or '无'}",
            f"最后事件: {data['last_event_type'] or '无'}",
            f"最后错误: {data['last_error_code'] or '无'}",
            f"token 状态: {data['token_status']}",
            f"建议: {_diagnosis_advice(data)}",
        ]
    )


def _diagnosis_advice(data: dict[str, object]) -> str:
    if data["connect_status"] == "connected" and data["binding_status"] == "active":
        return "可以开始对话"
    if data["connect_status"] in {"pending", "disconnected"}:
        return f"请重新获取连接信息并启动 BOT：/connect {data['bot_id']}"
    if data["connect_status"] == "authenticating":
        return "BOT 正在认证，请稍后重试"
    return "请检查 BOT 连接状态"


def _select_bot_prompt(db: Session, user_id: int, usage: str) -> str:
    items = list_user_bots(db, user_id)
    if not items:
        return "你的 BOT 列表为空。输入 /new-bot 创建 OpenClaw 员工助手接入槽位。"
    lines = [f"请选择 BOT ID，格式：{usage}"]
    for item in items:
        lines.append(f"{item['bot_id']} {item['name']}")
    return "\n".join(lines)


def text_reply(content: str) -> dict[str, str]:
    return {"reply_type": "text", "content": content}


def code_reply(content: str) -> dict[str, str]:
    return {"reply_type": "code", "content": content}
