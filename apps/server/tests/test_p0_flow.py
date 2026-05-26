import asyncio
import json
import queue
import re
import threading

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db.runtime_schema import ensure_sqlite_runtime_schema
from app.db.session import SessionLocal, engine
from app.models.bot import Bot, UserBotBinding
from app.models.friendship import Friendship
from app.services.bot_gateway_sessions import bot_gateway_sessions
from app.ws.employee import EmployeeWebSocketSessions
from tests.conftest import auth_headers


def register_and_login(client: TestClient) -> str:
    response = client.post(
        "/api/auth/register",
        json={
            "username": "zhangsan",
            "password": "secret123",
            "employee_id": "E001",
            "real_name": "张三",
        },
    )
    assert response.status_code == 200
    response = client.post("/api/auth/login", json={"username": "zhangsan", "password": "secret123"})
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


def command(client: TestClient, token: str, value: str) -> dict:
    response = client.post(
        "/api/default-bot/commands",
        headers=auth_headers(token),
        json={"command": value},
    )
    assert response.status_code == 200
    return response.json()["data"]


def register_user(
    client: TestClient, username: str, employee_id: str, real_name: str
) -> tuple[int, str]:
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "secret123",
            "employee_id": employee_id,
            "real_name": real_name,
        },
    )
    assert response.status_code == 200
    token = client.post(
        "/api/auth/login", json={"username": username, "password": "secret123"}
    ).json()["data"]["access_token"]
    return response.json()["data"]["user"]["id"], token


def accept_friendship(requester_id: int, addressee_id: int) -> None:
    with SessionLocal() as db:
        db.add(
            Friendship(
                requester_id=requester_id,
                addressee_id=addressee_id,
                status="accepted",
            )
        )
        db.commit()


def receive_json_with_timeout(websocket, timeout: float = 1.0) -> dict:
    result: queue.Queue[dict | BaseException] = queue.Queue(maxsize=1)

    def receive() -> None:
        try:
            result.put(websocket.receive_json())
        except BaseException as exc:
            result.put(exc)

    threading.Thread(target=receive, daemon=True).start()
    try:
        item = result.get(timeout=timeout)
    except queue.Empty as exc:
        raise AssertionError("timed out waiting for websocket event") from exc
    if isinstance(item, BaseException):
        raise item
    return item


def maybe_receive_json_with_timeout(websocket, timeout: float = 0.2) -> dict | None:
    try:
        return receive_json_with_timeout(websocket, timeout)
    except AssertionError:
        return None


def mark_bot_connected(user_id: int, bot_id: str) -> None:
    with SessionLocal() as db:
        model = db.query(Bot).filter(Bot.bot_id == bot_id).one()
        model.connect_status = "connected"
        db.add(UserBotBinding(user_id=user_id, bot_id=bot_id, binding_type=model.bot_type, status="active"))
        db.commit()


def test_sqlite_runtime_schema_remaps_old_bot_conversations(client: TestClient) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO conversations "
                "(id, conversation_type, owner_user_id, target_type, target_id, "
                "title, last_message_id, last_message_at, created_at, updated_at) "
                "VALUES "
                "('conv_old', 'bot', 1, 'bot', 'bot_old', '', NULL, NULL, "
                "'2026-05-25 00:00:00', '2026-05-25 00:00:00')"
            )
        )

    ensure_sqlite_runtime_schema(engine)

    with engine.begin() as connection:
        row = connection.execute(
            text("SELECT conversation_type, target_type FROM conversations WHERE id = 'conv_old'")
        ).one()
    assert row.conversation_type == "direct"
    assert row.target_type == "openclaw_bot"


def test_default_bot_conversation_is_created_only_by_ensure(client: TestClient) -> None:
    token = register_and_login(client)

    response = client.get("/api/conversations", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["data"]["items"] == []

    response = client.post(
        "/api/conversations/ensure",
        headers=auth_headers(token),
        json={"target_type": "system_default_bot", "target_id": "default_bot"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["created"] is True
    assert data["conversation"]["target_type"] == "system_default_bot"
    assert data["initial_messages"][0]["content"] == "你好！输入 /help 查看可用命令。"

    second = client.post(
        "/api/conversations/ensure",
        headers=auth_headers(token),
        json={"target_type": "system_default_bot", "target_id": "default_bot"},
    )
    assert second.status_code == 200
    assert second.json()["data"]["created"] is False
    assert second.json()["data"]["initial_messages"] == []


def test_conversation_messages_returns_initial_history(client: TestClient) -> None:
    token = register_and_login(client)
    conversation = client.post(
        "/api/conversations/ensure",
        headers=auth_headers(token),
        json={"target_type": "system_default_bot", "target_id": "default_bot"},
    ).json()["data"]["conversation"]

    response = client.get(f"/api/conversations/{conversation['id']}/messages", headers=auth_headers(token))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["has_more"] is False
    assert data["items"][0]["content"] == "你好！输入 /help 查看可用命令。"


def test_default_bot_command_persists_user_and_bot_messages(client: TestClient) -> None:
    token = register_and_login(client)
    conversation = client.post(
        "/api/conversations/ensure",
        headers=auth_headers(token),
        json={"target_type": "system_default_bot", "target_id": "default_bot"},
    ).json()["data"]["conversation"]

    response = client.post(
        f"/api/conversations/{conversation['id']}/messages",
        headers=auth_headers(token),
        json={"content": "/help", "content_type": "text"},
    )

    assert response.status_code == 200
    messages = response.json()["data"]["messages"]
    assert [item["sender_type"] for item in messages] == ["user", "bot"]
    assert messages[0]["content"] == "/help"
    assert "/new-bot" in messages[1]["content"]


def test_send_message_validates_content(client: TestClient) -> None:
    token = register_and_login(client)
    conversation = client.post(
        "/api/conversations/ensure",
        headers=auth_headers(token),
        json={"target_type": "system_default_bot", "target_id": "default_bot"},
    ).json()["data"]["conversation"]

    cases = [
        {"content": "   ", "content_type": "text"},
        {"content": "hello", "content_type": "image"},
        {"content": "x" * 4001, "content_type": "text"},
    ]
    for payload in cases:
        response = client.post(
            f"/api/conversations/{conversation['id']}/messages",
            headers=auth_headers(token),
            json=payload,
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "VALIDATION_FAILED"


def test_default_bot_creates_connects_and_masks_token(client: TestClient) -> None:
    token = register_and_login(client)

    conversations = client.get("/api/conversations", headers=auth_headers(token)).json()["data"]["items"]
    assert conversations == []

    reply = command(client, token, "/new-bot")
    bot_id = re.search(r"BOT_ID: (bot_[A-Z0-9]+)", reply["content"]).group(1)

    connect_reply = command(client, token, f"/connect {bot_id}")
    payload = json.loads(connect_reply["content"])
    assert payload["bot_id"] == bot_id
    assert payload["token"].startswith("ocb_live_")
    assert payload["token_status"] == "revealed_once"
    assert payload["gateway_url"] == "ws://testserver/bot-gateway/ws"

    masked_reply = command(client, token, f"/connect {bot_id}")
    assert "masked token: ocb_live_****_" in masked_reply["content"]
    assert f"confirm regenerate {bot_id}" in masked_reply["content"]

    regenerated = command(client, token, f"confirm regenerate {bot_id}")
    regenerated_payload = json.loads(regenerated["content"])
    assert regenerated_payload["token"].startswith("ocb_live_")
    assert regenerated_payload["token"] != payload["token"]


def test_default_bot_diagnose_connected_bot(client: TestClient) -> None:
    user_id, token = register_user(client, "zhangsan", "E001", "张三")
    bot_id = re.search(r"BOT_ID: (bot_[A-Z0-9]+)", command(client, token, "/new-bot")["content"]).group(1)
    mark_bot_connected(user_id, bot_id)

    reply = command(client, token, f"/diagnose {bot_id}")

    assert f"BOT_ID: {bot_id}" in reply["content"]
    assert "连接状态: connected" in reply["content"]
    assert "绑定状态: active" in reply["content"]
    assert "建议: 可以开始对话" in reply["content"]


def test_default_bot_diagnose_requires_bot_id(client: TestClient) -> None:
    token = register_and_login(client)

    reply = command(client, token, "/diagnose")

    assert "请输入要诊断的 BOT ID" in reply["content"]


def test_bot_gateway_auth_handshake_and_heartbeat(client: TestClient) -> None:
    token = register_and_login(client)
    bot_id = re.search(r"BOT_ID: (bot_[A-Z0-9]+)", command(client, token, "/new-bot")["content"]).group(1)
    connect_payload = json.loads(command(client, token, f"/connect {bot_id}")["content"])
    client.post(
        "/api/conversations/ensure",
        headers=auth_headers(token),
        json={"target_type": "openclaw_bot", "target_id": bot_id},
    )

    with client.websocket_connect("/bot-gateway/ws") as websocket:
        websocket.send_json(
            {
                "type": "auth",
                "request_id": "req_auth",
                "protocol_version": "bot-v1",
                "bot_id": bot_id,
                "token": connect_payload["token"],
            }
        )
        assert websocket.receive_json()["ok"] is True
        websocket.send_json(
            {
                "type": "handshake",
                "request_id": "req_handshake",
                "protocol_version": "bot-v1",
                "bot_id": bot_id,
                "runtime": {"name": "test", "version": "0.1.0"},
            }
        )
        assert websocket.receive_json()["type"] == "handshake.result"
        websocket.send_json(
            {
                "type": "heartbeat",
                "request_id": "req_heartbeat",
                "protocol_version": "bot-v1",
                "bot_id": bot_id,
            }
        )
        assert websocket.receive_json()["type"] == "heartbeat.result"

    bots = client.get("/api/bots", headers=auth_headers(token)).json()["data"]["items"]
    assert bots[0]["binding_status"] == "active"


def test_bot_gateway_pushes_status_changed_to_owner(client: TestClient) -> None:
    token = register_and_login(client)
    bot_id = re.search(r"BOT_ID: (bot_[A-Z0-9]+)", command(client, token, "/new-bot")["content"]).group(1)
    connect_payload = json.loads(command(client, token, f"/connect {bot_id}")["content"])

    with client.websocket_connect(f"/ws?token={token}") as employee_websocket:
        with client.websocket_connect("/bot-gateway/ws") as bot_websocket:
            bot_websocket.send_json(
                {
                    "type": "auth",
                    "request_id": "req_auth",
                    "protocol_version": "bot-v1",
                    "bot_id": bot_id,
                    "token": connect_payload["token"],
                }
            )
            assert bot_websocket.receive_json()["ok"] is True
            bot_websocket.send_json(
                {
                    "type": "handshake",
                    "request_id": "req_handshake",
                    "protocol_version": "bot-v1",
                    "bot_id": bot_id,
                    "runtime": {"name": "test", "version": "0.1.0"},
                }
            )
            assert bot_websocket.receive_json()["type"] == "handshake.result"

            event = receive_json_with_timeout(employee_websocket)
            api_bot = next(
                item
                for item in client.get("/api/bots", headers=auth_headers(token)).json()["data"]["items"]
                if item["bot_id"] == bot_id
            )

    assert event["type"] == "bot.status_changed"
    assert event["bot"] == api_bot


def test_bot_gateway_pushes_disconnected_on_socket_close(client: TestClient) -> None:
    token = register_and_login(client)
    bot_id = re.search(r"BOT_ID: (bot_[A-Z0-9]+)", command(client, token, "/new-bot")["content"]).group(1)
    connect_payload = json.loads(command(client, token, f"/connect {bot_id}")["content"])

    with client.websocket_connect(f"/ws?token={token}") as employee_websocket:
        with client.websocket_connect("/bot-gateway/ws") as bot_websocket:
            bot_websocket.send_json(
                {
                    "type": "auth",
                    "request_id": "req_auth",
                    "protocol_version": "bot-v1",
                    "bot_id": bot_id,
                    "token": connect_payload["token"],
                }
            )
            assert bot_websocket.receive_json()["ok"] is True
            bot_websocket.send_json(
                {
                    "type": "handshake",
                    "request_id": "req_handshake",
                    "protocol_version": "bot-v1",
                    "bot_id": bot_id,
                    "runtime": {"name": "test", "version": "0.1.0"},
                }
            )
            assert bot_websocket.receive_json()["type"] == "handshake.result"
            assert receive_json_with_timeout(employee_websocket)["bot"]["connect_status"] == "connected"

        event = receive_json_with_timeout(employee_websocket)

    assert event["type"] == "bot.status_changed"
    assert event["bot"]["bot_id"] == bot_id
    assert event["bot"]["connect_status"] == "disconnected"
    assert event["bot"]["binding_status"] == "active"
    assert "last_seen_at" in event["bot"]
    assert "first_connected_at" in event["bot"]


def test_employee_send_to_user_removes_stale_socket_on_send_failure() -> None:
    class BrokenWebSocket:
        async def send_json(self, payload: dict[str, object]) -> None:
            raise RuntimeError("socket closed")

    sessions = EmployeeWebSocketSessions()
    websocket = BrokenWebSocket()
    sessions._sessions[1] = {websocket}

    asyncio.run(sessions.send_to_user(1, {"type": "ping"}))

    assert 1 not in sessions._sessions


def test_bot_gateway_auth_only_disconnect_marks_bot_disconnected(client: TestClient) -> None:
    token = register_and_login(client)
    bot_id = re.search(r"BOT_ID: (bot_[A-Z0-9]+)", command(client, token, "/new-bot")["content"]).group(1)
    connect_payload = json.loads(command(client, token, f"/connect {bot_id}")["content"])

    with client.websocket_connect("/bot-gateway/ws") as bot_websocket:
        bot_websocket.send_json(
            {
                "type": "auth",
                "request_id": "req_auth",
                "protocol_version": "bot-v1",
                "bot_id": bot_id,
                "token": connect_payload["token"],
            }
        )
        assert bot_websocket.receive_json()["ok"] is True

    with SessionLocal() as db:
        status = db.query(Bot).filter(Bot.bot_id == bot_id).one().connect_status

    assert status == "disconnected"


def test_bot_gateway_stale_auth_only_close_does_not_disconnect_live_session(
    client: TestClient,
) -> None:
    token = register_and_login(client)
    bot_id = re.search(r"BOT_ID: (bot_[A-Z0-9]+)", command(client, token, "/new-bot")["content"]).group(1)
    connect_payload = json.loads(command(client, token, f"/connect {bot_id}")["content"])

    with client.websocket_connect(f"/ws?token={token}") as employee_websocket:
        with client.websocket_connect("/bot-gateway/ws") as stale_websocket:
            stale_websocket.send_json(
                {
                    "type": "auth",
                    "request_id": "req_stale_auth",
                    "protocol_version": "bot-v1",
                    "bot_id": bot_id,
                    "token": connect_payload["token"],
                }
            )
            assert stale_websocket.receive_json()["ok"] is True

            with client.websocket_connect("/bot-gateway/ws") as live_websocket:
                live_websocket.send_json(
                    {
                        "type": "auth",
                        "request_id": "req_live_auth",
                        "protocol_version": "bot-v1",
                        "bot_id": bot_id,
                        "token": connect_payload["token"],
                    }
                )
                assert live_websocket.receive_json()["ok"] is True
                live_websocket.send_json(
                    {
                        "type": "handshake",
                        "request_id": "req_live_handshake",
                        "protocol_version": "bot-v1",
                        "bot_id": bot_id,
                        "runtime": {"name": "test", "version": "0.1.0"},
                    }
                )
                assert live_websocket.receive_json()["type"] == "handshake.result"
                assert receive_json_with_timeout(employee_websocket)["bot"]["connect_status"] == "connected"

                stale_websocket.close()
                event = maybe_receive_json_with_timeout(employee_websocket)

                with SessionLocal() as db:
                    status = db.query(Bot).filter(Bot.bot_id == bot_id).one().connect_status

                assert event is None
                assert status == "connected"


def test_bot_gateway_does_not_disconnect_when_closing_socket_is_not_current(
    client: TestClient,
) -> None:
    token = register_and_login(client)
    bot_id = re.search(r"BOT_ID: (bot_[A-Z0-9]+)", command(client, token, "/new-bot")["content"]).group(1)
    connect_payload = json.loads(command(client, token, f"/connect {bot_id}")["content"])

    try:
        with client.websocket_connect(f"/ws?token={token}") as employee_websocket:
            with client.websocket_connect("/bot-gateway/ws") as bot_websocket:
                bot_websocket.send_json(
                    {
                        "type": "auth",
                        "request_id": "req_auth",
                        "protocol_version": "bot-v1",
                        "bot_id": bot_id,
                        "token": connect_payload["token"],
                    }
                )
                assert bot_websocket.receive_json()["ok"] is True
                bot_websocket.send_json(
                    {
                        "type": "handshake",
                        "request_id": "req_handshake",
                        "protocol_version": "bot-v1",
                        "bot_id": bot_id,
                        "runtime": {"name": "test", "version": "0.1.0"},
                    }
                )
                assert bot_websocket.receive_json()["type"] == "handshake.result"
                assert receive_json_with_timeout(employee_websocket)["bot"]["connect_status"] == "connected"
                bot_gateway_sessions.register(bot_id, object())

            event = maybe_receive_json_with_timeout(employee_websocket)
    finally:
        bot_gateway_sessions._sessions.pop(bot_id, None)

    with SessionLocal() as db:
        status = db.query(Bot).filter(Bot.bot_id == bot_id).one().connect_status

    assert event is None
    assert status == "connected"


def test_startup_cleanup_resets_runtime_bot_connections(client: TestClient) -> None:
    token = register_and_login(client)
    connected_id = re.search(
        r"BOT_ID: (bot_[A-Z0-9]+)", command(client, token, "/new-bot")["content"]
    ).group(1)
    authenticating_id = re.search(
        r"BOT_ID: (bot_[A-Z0-9]+)", command(client, token, "/new-bot")["content"]
    ).group(1)
    pending_id = re.search(
        r"BOT_ID: (bot_[A-Z0-9]+)", command(client, token, "/new-bot")["content"]
    ).group(1)

    with SessionLocal() as db:
        db.query(Bot).filter(Bot.bot_id == connected_id).one().connect_status = "connected"
        db.query(Bot).filter(Bot.bot_id == authenticating_id).one().connect_status = "authenticating"
        db.query(Bot).filter(Bot.bot_id == pending_id).one().connect_status = "pending"
        db.commit()

    from app.services.bots import reset_runtime_bot_connections

    reset_runtime_bot_connections()

    with SessionLocal() as db:
        statuses = {
            bot.bot_id: bot.connect_status
            for bot in db.query(Bot).filter(Bot.bot_id.in_([connected_id, authenticating_id, pending_id]))
        }

    assert statuses == {
        connected_id: "disconnected",
        authenticating_id: "disconnected",
        pending_id: "pending",
    }


def test_users_include_relationship_and_presence(client: TestClient) -> None:
    alice_token = register_and_login(client)
    response = client.post(
        "/api/auth/register",
        json={
            "username": "lisi",
            "password": "secret123",
            "employee_id": "E002",
            "real_name": "李四",
        },
    )
    assert response.status_code == 200

    users = client.get("/api/users", headers=auth_headers(alice_token)).json()["data"]["items"]
    self_item = next(item for item in users if item["username"] == "zhangsan")
    other_item = next(item for item in users if item["username"] == "lisi")

    assert self_item["relationship"] == "self"
    assert self_item["online"] is True
    assert self_item["last_seen_at"] is not None
    assert other_item["relationship"] == "none"
    assert other_item["online"] is False
    assert other_item["last_seen_at"] is not None
    assert self_item["last_seen_at"].endswith("Z")
    assert other_item["last_seen_at"].endswith("Z")


def test_contacts_include_users_default_bot_and_openclaw_bots(client: TestClient) -> None:
    user_id, token = register_user(client, "zhangsan", "E001", "张三")
    register_user(client, "lisi", "E002", "李四")
    bot_id = re.search(r"BOT_ID: (bot_[A-Z0-9]+)", command(client, token, "/new-bot")["content"]).group(1)
    mark_bot_connected(user_id, bot_id)

    response = client.get("/api/contacts", headers=auth_headers(token))

    assert response.status_code == 200
    data = response.json()["data"]
    assert [item["contact_type"] for item in data["ai"]] == ["system_default_bot", "openclaw_bot"]
    assert {item["contact_type"] for item in data["all"]} == {
        "user",
        "system_default_bot",
        "openclaw_bot",
    }
    assert {item["id"] for item in data["all"]} >= {"default_bot", bot_id, str(user_id)}
    openclaw = next(item for item in data["all"] if item["id"] == bot_id)
    assert openclaw["online"] is True
    assert openclaw["bot"]["binding_status"] == "active"


def test_create_friend_request_updates_relationship(client: TestClient) -> None:
    alice_token = register_and_login(client)
    response = client.post(
        "/api/auth/register",
        json={
            "username": "lisi",
            "password": "secret123",
            "employee_id": "E002",
            "real_name": "李四",
        },
    )
    assert response.status_code == 200
    bob_id = response.json()["data"]["user"]["id"]

    response = client.post(f"/api/friends/{bob_id}", headers=auth_headers(alice_token))

    assert response.status_code == 200
    assert response.json()["data"]["relationship"] == "pending_out"
    users = client.get("/api/users", headers=auth_headers(alice_token)).json()["data"]["items"]
    bob_item = next(item for item in users if item["id"] == bob_id)
    assert bob_item["relationship"] == "pending_out"


def test_bot_message_roundtrip_waits_for_connected_bot_reply(client: TestClient, monkeypatch) -> None:
    user_id, token = register_user(client, "zhangsan", "E001", "张三")
    bot_id = re.search(r"BOT_ID: (bot_[A-Z0-9]+)", command(client, token, "/new-bot")["content"]).group(1)
    command(client, token, f"/connect {bot_id}")
    mark_bot_connected(user_id, bot_id)
    conversation = client.post(
        "/api/conversations/ensure",
        headers=auth_headers(token),
        json={"target_type": "openclaw_bot", "target_id": bot_id},
    ).json()["data"]["conversation"]

    async def fake_request_reply(**kwargs):
        assert kwargs["bot_id"] == bot_id
        assert kwargs["conversation_id"] == conversation["id"]
        assert kwargs["text"] == "hello"
        return {"content": {"type": "text", "text": "openclaw says hi"}}

    monkeypatch.setattr(
        "app.services.messages.bot_gateway_sessions.request_reply", fake_request_reply
    )

    response = client.post(
        f"/api/conversations/{conversation['id']}/messages",
        headers=auth_headers(token),
        json={"content": "hello", "content_type": "text"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert [item["sender_type"] for item in data["messages"]] == ["user", "bot"]
    assert data["messages"][1]["content"] == "openclaw says hi"

    history = client.get(
        f"/api/conversations/{conversation['id']}/messages",
        headers=auth_headers(token),
    ).json()["data"]["items"]
    assert any(item["content"] == "hello" for item in history)
    assert any(item["content"] == "openclaw says hi" for item in history)


def test_openclaw_disconnected_returns_persisted_system_message(client: TestClient) -> None:
    token = register_and_login(client)
    bot_id = re.search(r"BOT_ID: (bot_[A-Z0-9]+)", command(client, token, "/new-bot")["content"]).group(1)
    conversation = client.post(
        "/api/conversations/ensure",
        headers=auth_headers(token),
        json={"target_type": "openclaw_bot", "target_id": bot_id},
    ).json()["data"]["conversation"]

    response = client.post(
        f"/api/conversations/{conversation['id']}/messages",
        headers=auth_headers(token),
        json={"content": "hello", "content_type": "text"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "BOT_NOT_CONNECTED"


def test_employee_message_creates_sender_and_receiver_copies(client: TestClient) -> None:
    alice_id, alice_token = register_user(client, "alice", "E101", "Alice")
    bob_id, bob_token = register_user(client, "bob", "E102", "Bob")
    accept_friendship(alice_id, bob_id)

    alice_conversation = client.post(
        "/api/conversations/ensure",
        headers=auth_headers(alice_token),
        json={"target_type": "user", "target_id": str(bob_id)},
    ).json()["data"]["conversation"]

    response = client.post(
        f"/api/conversations/{alice_conversation['id']}/messages",
        headers=auth_headers(alice_token),
        json={"content": "hello bob", "content_type": "text"},
    )

    assert response.status_code == 200
    sent = response.json()["data"]["messages"][0]
    assert sent["sender_type"] == "user"
    assert sent["sender_id"] == str(alice_id)
    assert sent["content"] == "hello bob"

    bob_conversations = client.get(
        "/api/conversations", headers=auth_headers(bob_token)
    ).json()["data"]["items"]
    bob_conversation = next(item for item in bob_conversations if item["target_id"] == str(alice_id))
    bob_history = client.get(
        f"/api/conversations/{bob_conversation['id']}/messages",
        headers=auth_headers(bob_token),
    ).json()["data"]["items"]

    assert bob_history[-1]["content"] == "hello bob"
    assert bob_history[-1]["sender_id"] == str(alice_id)
    assert bob_history[-1]["client_message_id"] == sent["client_message_id"]


def test_employee_message_requires_accepted_friendship(client: TestClient) -> None:
    _, alice_token = register_user(client, "alice", "E101", "Alice")
    bob_id, _ = register_user(client, "bob", "E102", "Bob")

    response = client.post(
        "/api/conversations/ensure",
        headers=auth_headers(alice_token),
        json={"target_type": "user", "target_id": str(bob_id)},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_employee_message_pushes_events_to_online_receiver(
    client: TestClient, monkeypatch
) -> None:
    alice_id, alice_token = register_user(client, "alice", "E101", "Alice")
    bob_id, _ = register_user(client, "bob", "E102", "Bob")
    accept_friendship(alice_id, bob_id)
    alice_conversation = client.post(
        "/api/conversations/ensure",
        headers=auth_headers(alice_token),
        json={"target_type": "user", "target_id": str(bob_id)},
    ).json()["data"]["conversation"]
    pushed: list[tuple[int, dict[str, object]]] = []

    async def fake_send_to_user(user_id: int, payload: dict[str, object]) -> None:
        pushed.append((user_id, payload))

    monkeypatch.setattr("app.api.conversations.employee_ws_sessions.send_to_user", fake_send_to_user)

    response = client.post(
        f"/api/conversations/{alice_conversation['id']}/messages",
        headers=auth_headers(alice_token),
        json={"content": "realtime hello", "content_type": "text"},
    )

    assert response.status_code == 200
    assert [item[0] for item in pushed] == [bob_id, bob_id]
    assert [item[1]["type"] for item in pushed] == ["message.new", "conversation.updated"]
    assert pushed[0][1]["message"]["content"] == "realtime hello"
    assert pushed[1][1]["conversation"]["target_id"] == str(alice_id)
