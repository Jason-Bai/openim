# Unified Conversations Messages Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist conversations and messages for default BOT, OpenClaw BOT, and employee direct messages, with minimal realtime employee WebSocket push.

**Architecture:** Backend introduces one durable conversation/message path and dispatches messages by `target_type`. Frontend removes long-lived local chat arrays and renders conversations/messages from TanStack Query, using short-lived optimistic messages only during sends. Employee-to-employee realtime uses a small `/ws` session manager; persisted history remains the source of truth.

**Tech Stack:** FastAPI, SQLAlchemy 2.x, pytest, React, TypeScript, TanStack Query, Zustand, Ant Design, native WebSocket.

**Spec:** `/Users/baiyu/workspaces/gitlab/openim/docs/superpowers/specs/2026-05-25-conversation-message-persistence-design.md`

---

## File Structure

Backend create/modify:

- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/core/security.py`
  - Add `create_message_id()` and `create_client_message_id()`.
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/core/errors.py`
  - Register conversation/message/WebSocket error codes with correct HTTP statuses.
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/models/conversation.py`
  - Normalize `conversation_type = direct`, add `title`, indexes, unique constraint.
- Create: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/models/message.py`
  - SQLAlchemy message model.
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/models/__init__.py`
  - Import `Message`.
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/db/runtime_schema.py`
  - SQLite-only migration shims for local/test databases.
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/alembic/versions/0001_p0_schema.py`
  - Keep fresh Alembic-created databases aligned with the new conversation/message schema.
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/alembic/env.py`
  - Import model metadata consistently for future autogenerate.
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/services/conversations.py`
  - Replace auto default conversation creation with explicit `ensure_conversation`.
- Create: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/services/messages.py`
  - Message persistence, target dispatch, history listing, conversation last-message updates.
- Create: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/ws/employee_ws.py`
  - Employee WebSocket manager and `/ws` endpoint.
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/api/conversations.py`
  - Add `ensure`, `messages`, and unified send endpoints.
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/api/auth.py`
  - Stop creating default BOT conversation on register/login.
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/services/bots.py`
  - Stop creating OpenClaw conversation during handshake.
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/main.py`
  - Include employee WebSocket router.
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/tests/test_p0_flow.py`
  - Update old expectations and add persistence/realtime coverage.

Frontend create/modify:

- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/web/src/api/openim.ts`
  - Add conversation detail/message types and unified API functions.
- Create: `/Users/baiyu/workspaces/gitlab/openim/apps/web/src/api/wsClient.ts`
  - Minimal employee WebSocket client.
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/web/src/pages/App.tsx`
  - Replace local session/message arrays with conversation/message queries.
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/web/src/styles.css`
  - Only if needed for persisted/realtime UI states.
- Create: `/Users/baiyu/workspaces/gitlab/openim/scripts/e2e-conversations.mjs`
  - Local REST smoke test for default BOT conversation persistence.

---

## Chunk 1: Backend Conversation And Message Persistence

### Task 0: Add runtime schema migration details

**Files:**
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/db/runtime_schema.py`
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/alembic/versions/0001_p0_schema.py`
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/alembic/env.py`

- [ ] **Step 1: Write the migration requirements into the implementation checklist**

`ensure_sqlite_runtime_schema(engine)` must handle local SQLite databases that already have old P0 tables:

- create `messages` if absent;
- add `conversations.title` if absent, defaulting to `""`;
- normalize existing `conversations.conversation_type = "bot"` to `"direct"`;
- normalize existing `conversations.target_type = "bot"` to `"openclaw_bot"`;
- update Alembic revision `0001_p0_schema.py` so fresh databases include `conversations.title`, message table, conversation indexes, message indexes, and `last_message_id` FK.
- ensure Alembic `env.py` imports all models through `app.models` so future autogenerate sees `Message`.

- [ ] **Step 2: Add a failing runtime migration test**

Add a test that creates an old-style conversation row with `target_type = "bot"` before calling `ensure_sqlite_runtime_schema(engine)`, then asserts the row becomes `target_type = "openclaw_bot"` and `conversation_type = "direct"`.

Run:

```bash
cd /Users/baiyu/workspaces/gitlab/openim/apps/server
uv run pytest tests/test_p0_flow.py::test_sqlite_runtime_schema_remaps_old_bot_conversations -q
```

Expected: FAIL until runtime migration logic exists.

- [ ] **Step 3: Implement runtime migration**

Use `inspect(engine).get_columns("conversations")` and `connection.execute(text("UPDATE conversations SET target_type = 'openclaw_bot' WHERE target_type = 'bot'"))` style statements. Do not drop existing data.

- [ ] **Step 4: Verify**

Run:

```bash
cd /Users/baiyu/workspaces/gitlab/openim/apps/server
uv run pytest tests/test_p0_flow.py::test_sqlite_runtime_schema_remaps_old_bot_conversations -q
```

Expected: PASS.

- [ ] **Step 5: Verify Alembic schema file contains new tables/indexes**

Run:

```bash
cd /Users/baiyu/workspaces/gitlab/openim/apps/server
rg -n "create_table\\(\"messages\"|title|idx_messages_conversation_created|idx_conversations_owner_sort|last_message_id" alembic/versions/0001_p0_schema.py
```

Expected: all listed schema elements are present.

- [ ] **Step 6: Run Alembic upgrade against an empty SQLite database**

Run:

```bash
cd /Users/baiyu/workspaces/gitlab/openim/apps/server
rm -f /tmp/openim-alembic-test.db
DATABASE_URL=sqlite:////tmp/openim-alembic-test.db uv run alembic upgrade head
DATABASE_URL=sqlite:////tmp/openim-alembic-test.db uv run python - <<'PY'
from sqlalchemy import create_engine, inspect
engine = create_engine("sqlite:////tmp/openim-alembic-test.db")
inspector = inspect(engine)
assert "messages" in inspector.get_table_names()
conversation_columns = {column["name"] for column in inspector.get_columns("conversations")}
assert "title" in conversation_columns
assert "last_message_id" in conversation_columns
print("alembic schema smoke passed")
PY
```

Expected: prints `alembic schema smoke passed`.

### Task 0.5: Register backend error codes

**Files:**
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/core/errors.py`

- [ ] **Step 1: Add error specs**

Add or confirm:

```python
"CONVERSATION_NOT_FOUND": ErrorSpec(404),
"MESSAGE_DELIVERY_FAILED": ErrorSpec(500, retryable=True),
"AUTH_EXPIRED": ErrorSpec(401),
```

Keep existing `FORBIDDEN` and `VALIDATION_FAILED`.

- [ ] **Step 2: Verify error mapping**

Run:

```bash
cd /Users/baiyu/workspaces/gitlab/openim/apps/server
uv run python - <<'PY'
from app.core.errors import ApiError
assert ApiError("CONVERSATION_NOT_FOUND", "x").http_status == 404
assert ApiError("MESSAGE_DELIVERY_FAILED", "x").retryable is True
assert ApiError("AUTH_EXPIRED", "x").http_status == 401
print("error specs smoke passed")
PY
```

Expected: prints `error specs smoke passed`.

### Task 1: Write failing tests for explicit conversation creation

**Files:**
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/tests/test_p0_flow.py`

- [ ] **Step 1: Add tests**

Add tests that assert registration/login do not create conversations, `ensure` creates default BOT conversation with initial message, and repeated `ensure` is idempotent.

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /Users/baiyu/workspaces/gitlab/openim/apps/server
uv run pytest tests/test_p0_flow.py::test_default_bot_conversation_is_created_only_by_ensure -q
```

Expected: FAIL because `/api/conversations` currently auto-creates default BOT conversation and `/api/conversations/ensure` does not exist.

### Task 2: Add message model and ID helpers

**Files:**
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/core/security.py`
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/models/conversation.py`
- Create: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/models/message.py`
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/models/__init__.py`

- [ ] **Step 1: Add ID helpers**

```python
def create_message_id() -> str:
    return f"msg_{ulid.new()}"


def create_client_message_id() -> str:
    return f"cmsg_{ulid.new()}"
```

- [ ] **Step 2: Update conversation model**

Add `title`, constraints, and indexes. Keep existing columns compatible.

```python
__table_args__ = (
    UniqueConstraint("owner_user_id", "target_type", "target_id", name="uq_conversations_owner_target"),
    Index("idx_conversations_owner_sort", "owner_user_id", "last_message_at", "updated_at"),
)

title: Mapped[str] = mapped_column(String(120), nullable=False, default="")
last_message_id: Mapped[str | None] = mapped_column(
    String(64),
    ForeignKey("messages.id", ondelete="SET NULL", use_alter=True),
    nullable=True,
)
```

- [ ] **Step 3: Create message model**

```python
class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index("idx_messages_conversation_created", "conversation_id", "created_at", "id"),
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    client_message_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    sender_type: Mapped[str] = mapped_column(String(16), nullable=False)
    sender_id: Mapped[str] = mapped_column(String(64), nullable=False)
    content_type: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="sent")
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=now_utc, nullable=False)
```

- [ ] **Step 4: Run model import check**

Run:

```bash
cd /Users/baiyu/workspaces/gitlab/openim/apps/server
uv run python -c "from app.models import Conversation, Message; print(Conversation.__tablename__, Message.__tablename__)"
```

Expected: prints `conversations messages`.

Run the current model test again after adding the `last_message_id` foreign key:

```bash
cd /Users/baiyu/workspaces/gitlab/openim/apps/server
uv run pytest tests/test_p0_flow.py::test_default_bot_conversation_is_created_only_by_ensure -q
```

Expected: still FAIL for missing route/behavior, not because metadata creation fails.

### Task 3: Implement explicit ensure/list conversation behavior

**Files:**
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/services/conversations.py`
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/api/conversations.py`
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/api/auth.py`
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/services/bots.py`

- [ ] **Step 1: Remove auto creation**

Remove `ensure_default_bot_conversation` calls from register/login and from `list_conversations`. Remove `ensure_bot_conversation` from bot handshake code.

- [ ] **Step 2: Implement target title and authorization helpers**

In `services/conversations.py`, add:

```python
def ensure_conversation(db: Session, user: User, target_type: str, target_id: str) -> tuple[Conversation, bool, list[Message]]:
    # implemented in Task 3; returns conversation, created flag, initial messages
    raise NotImplementedError
```

Rules:

- `system_default_bot/default_bot`: always allowed.
- `openclaw_bot/bot_id`: only owner or active binding.
- `user/user_id`: only `friendships.status == "accepted"` in either direction; self returns `FORBIDDEN`.

- [ ] **Step 3: Insert initial messages only on creation**

Default BOT and OpenClaw BOT get initial messages. User conversations do not.

- [ ] **Step 4: Implement endpoints**

Add:

```python
@router.post("/ensure")
def ensure_conversation_endpoint(
    payload: EnsureConversationRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
)
```

Return `conversation`, `created`, `initial_messages` using the spec schema.

Update `GET /api/conversations` at the same time:

- return `title`, `last_message`, `last_message_id`, `last_message_at`, and `online`;
- sort by `COALESCE(last_message_at, updated_at) DESC`;
- never call `ensure_default_bot_conversation`;
- for `openclaw_bot`, derive `online` from `connect_status == "connected"`;
- for `system_default_bot`, `online = true`;
- for `user`, derive `online` from the target user.

- [ ] **Step 5: Run test**

Run:

```bash
cd /Users/baiyu/workspaces/gitlab/openim/apps/server
uv run pytest tests/test_p0_flow.py::test_default_bot_conversation_is_created_only_by_ensure -q
```

Expected: PASS.

- [ ] **Step 6: Add and run list schema/sort test**

Add `test_conversation_list_returns_required_schema_and_sorts_by_last_message`.

Run:

```bash
cd /Users/baiyu/workspaces/gitlab/openim/apps/server
uv run pytest tests/test_p0_flow.py::test_conversation_list_returns_required_schema_and_sorts_by_last_message -q
```

Expected after implementation: PASS.

### Task 4: Implement history listing

**Files:**
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/tests/test_p0_flow.py`
- Create: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/services/messages.py`
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/api/conversations.py`

- [ ] **Step 1: Add failing history test**

```python
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
```

Also add `test_conversation_messages_supports_before_cursor_and_has_more` after send is implemented in Task 5. That test should create at least three messages, request `limit=2`, assert `has_more is True`, then request `before=<next_before>` and assert older messages are returned.

- [ ] **Step 2: Verify failure**

Run:

```bash
cd /Users/baiyu/workspaces/gitlab/openim/apps/server
uv run pytest tests/test_p0_flow.py::test_conversation_messages_returns_initial_history -q
```

Expected: FAIL because messages endpoint does not exist.

- [ ] **Step 3: Implement `list_messages`**

Validate conversation ownership. Return latest `limit` capped at 100, oldest-to-newest. Implement cursor behavior:

- `before` is a message id;
- locate the cursor message inside the same conversation;
- return messages with `(created_at, id)` older than the cursor;
- `next_before` is the first returned message id when more older rows exist, otherwise `null`;
- `has_more` is true when at least one older row remains.

- [ ] **Step 4: Add route**

```python
@router.get("/{conversation_id}/messages")
def conversation_messages(
    conversation_id: str,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
    limit: int = 50,
    before: str | None = None,
)
```

- [ ] **Step 5: Verify**

Run:

```bash
cd /Users/baiyu/workspaces/gitlab/openim/apps/server
uv run pytest tests/test_p0_flow.py::test_conversation_messages_returns_initial_history -q
```

Expected: PASS.

- [ ] **Step 6: Verify cursor pagination after Task 5**

Run:

```bash
cd /Users/baiyu/workspaces/gitlab/openim/apps/server
uv run pytest tests/test_p0_flow.py::test_conversation_messages_supports_before_cursor_and_has_more -q
```

Expected after send implementation: PASS.

---

## Chunk 2: Unified Send And Employee Realtime

### Task 5: Implement default BOT send through conversation messages

**Files:**
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/tests/test_p0_flow.py`
- Create/Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/services/messages.py`
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/api/conversations.py`

- [ ] **Step 1: Add failing test**

```python
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
```

- [ ] **Step 2: Verify failure**

Run:

```bash
cd /Users/baiyu/workspaces/gitlab/openim/apps/server
uv run pytest tests/test_p0_flow.py::test_default_bot_command_persists_user_and_bot_messages -q
```

Expected: FAIL because send endpoint does not exist.

- [ ] **Step 3: Implement validation**

Reject unsupported `content_type`, whitespace-only content, and content over 4000 chars with `VALIDATION_FAILED`.

Add `test_send_message_validates_content` covering all three cases.

- [ ] **Step 4: Implement default BOT dispatch**

Call existing `handle_command`, persist user and bot messages, update conversation last-message fields.

- [ ] **Step 5: Verify**

Run:

```bash
cd /Users/baiyu/workspaces/gitlab/openim/apps/server
uv run pytest tests/test_p0_flow.py::test_default_bot_command_persists_user_and_bot_messages -q
uv run pytest tests/test_p0_flow.py::test_send_message_validates_content -q
```

Expected: PASS.

### Task 6: Implement OpenClaw BOT send persistence and failure contract

**Files:**
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/tests/test_p0_flow.py`
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/services/messages.py`
- Keep compatibility: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/api/bot_messages.py`

- [ ] **Step 1: Add roundtrip persistence test**

Adapt existing `test_bot_message_roundtrip_waits_for_connected_bot_reply` to use:

```http
POST /api/conversations/{conversation_id}/messages
```

Assert response contains user message and bot reply, and `GET /messages` returns both after refresh-like fetch.

Run:

```bash
cd /Users/baiyu/workspaces/gitlab/openim/apps/server
uv run pytest tests/test_p0_flow.py::test_bot_message_roundtrip_waits_for_connected_bot_reply -q
```

Expected before implementation: FAIL because the test has been updated to use the unified endpoint.

- [ ] **Step 2: Add disconnected failure test**

Send to an OpenClaw conversation when no gateway session is connected. Assert HTTP 200, `ok: true`, user message + system failure message are persisted.

Run:

```bash
cd /Users/baiyu/workspaces/gitlab/openim/apps/server
uv run pytest tests/test_p0_flow.py::test_openclaw_disconnected_returns_persisted_system_message -q
```

Expected before implementation: FAIL.

- [ ] **Step 3: Implement `openclaw_bot` dispatch**

Make the unified send endpoint and message service async in this task, before running OpenClaw tests:

```python
@router.post("/{conversation_id}/messages")
async def send_conversation_message(
    conversation_id: str,
    payload: SendMessageRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
):
    result = await send_message(db, user, conversation_id, payload)
    db.commit()
    await push_delivery_events(result.delivery_events)
    return ok(result.payload, request_id_from(request))
```

Use existing async `bot_gateway_sessions.request_reply`. On success persist bot reply. On disconnected/timeout persist system failure message and return success. For non-employee targets, `delivery_events` is empty.

- [ ] **Step 4: Preserve old compatibility endpoint**

Update `/api/bots/{bot_id}/messages` to call the same message service internally or leave it working with persisted messages if low-risk. Do not use it from frontend.

Compatibility note: existing tests should continue passing unless this plan explicitly rewrites them to the unified endpoint.

- [ ] **Step 5: Verify**

Run:

```bash
cd /Users/baiyu/workspaces/gitlab/openim/apps/server
uv run pytest tests/test_p0_flow.py::test_bot_message_roundtrip_waits_for_connected_bot_reply -q
uv run pytest tests/test_p0_flow.py::test_openclaw_disconnected_returns_persisted_system_message -q
```

Expected: PASS.

### Task 7: Implement employee-to-employee persistence

**Files:**
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/tests/test_p0_flow.py`
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/services/messages.py`
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/services/conversations.py`

- [ ] **Step 1: Add friend setup helper in tests**

Create explicit helpers in `tests/test_p0_flow.py`:

```python
def register_user(client: TestClient, username: str, employee_id: str, real_name: str) -> tuple[int, str]:
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "secret123", "employee_id": employee_id, "real_name": real_name},
    )
    assert response.status_code == 200
    user_id = response.json()["data"]["user"]["id"]
    token = client.post("/api/auth/login", json={"username": username, "password": "secret123"}).json()["data"]["access_token"]
    return user_id, token


def accept_friendship(client: TestClient, requester_id: int, requester_token: str, addressee_id: int) -> None:
    response = client.post(f"/api/friends/{addressee_id}", headers=auth_headers(requester_token))
    assert response.status_code == 200
    from app.db.session import SessionLocal
    from app.models.friendship import Friendship
    with SessionLocal() as db:
        friendship = db.query(Friendship).filter(
            Friendship.requester_id == requester_id,
            Friendship.addressee_id == addressee_id,
        ).one()
        friendship.status = "accepted"
        db.commit()
```

- [ ] **Step 2: Add failing sender/receiver persistence test**

Assert A send creates A conversation message and B reverse conversation/message with same `client_message_id`.

Run:

```bash
cd /Users/baiyu/workspaces/gitlab/openim/apps/server
uv run pytest tests/test_p0_flow.py::test_employee_message_creates_sender_and_receiver_copies -q
```

Expected before implementation: FAIL.

- [ ] **Step 3: Implement transaction**

Within one DB transaction, ensure receiver conversation, insert both rows, update both conversations.

- [ ] **Step 4: Verify non-friend forbidden**

Add and pass a test that non-friend ensure/send returns 403 `FORBIDDEN`.

Run:

```bash
cd /Users/baiyu/workspaces/gitlab/openim/apps/server
uv run pytest tests/test_p0_flow.py::test_employee_message_requires_accepted_friendship -q
uv run pytest tests/test_p0_flow.py::test_employee_message_creates_sender_and_receiver_copies -q
```

Expected: PASS.

### Task 8: Implement employee WebSocket push

**Files:**
- Create: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/ws/employee_ws.py`
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/main.py`
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/app/services/messages.py`
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/tests/test_p0_flow.py`

- [ ] **Step 1: Add failing realtime test**

Use `client.websocket_connect(f"/ws?token={bob_token}")`, send A->B, assert B receives `message.new` and `conversation.updated`.

- [ ] **Step 2: Implement manager**

```python
class EmployeeWsManager:
    def connect(self, user_id: int, websocket: WebSocket) -> None:
        self._connections.setdefault(user_id, set()).add(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        sockets = self._connections.get(user_id)
        if sockets:
            sockets.discard(websocket)

    async def send_to_user(self, user_id: int, payload: dict[str, object]) -> None:
        for websocket in list(self._connections.get(user_id, set())):
            await websocket.send_json(payload)
```

Own the singleton in this file:

```python
employee_ws_manager = EmployeeWsManager()
```

- [ ] **Step 3: Implement `/ws` endpoint**

Decode token from query parameter. Accept, register, keep receiving until disconnect. Invalid token closes connection.

- [ ] **Step 4: Push after DB commit**

The unified send route was made async in Task 6. Keep that boundary here:

```python
@router.post("/{conversation_id}/messages")
async def send_conversation_message(
    conversation_id: str,
    payload: SendMessageRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
):
    result = await send_message(db, user, conversation_id, payload)
    db.commit()
    await push_delivery_events(result.delivery_events)
    return ok(result.payload, request_id_from(request))
```

`messages.py` owns persistence and returns `delivery_events`; `employee_ws.py` owns WebSocket sessions and best-effort push. If push raises, catch/log and still return success.

- [ ] **Step 5: Verify**

Run:

```bash
cd /Users/baiyu/workspaces/gitlab/openim/apps/server
uv run pytest tests/test_p0_flow.py::test_employee_message_realtime_pushes_to_online_receiver -q
```

Expected: PASS.

---

## Chunk 3: Frontend Unified Conversation Flow

Frontend note: this workspace currently has no DOM/component test runner such as Vitest + Testing Library. For this plan, frontend verification is split into TypeScript build checks plus a Node smoke script in Chunk 4 that verifies the backend contracts the UI depends on. Browser QA remains required for visual/interaction behavior.

### Task 9: Add frontend API types and calls

**Files:**
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/web/src/api/openim.ts`

- [ ] **Step 1: Add types**

Add `Conversation`, `ChatMessage`, `EnsureConversationResponse`, `MessagesResponse`, `SendMessageResponse` matching the spec.

- [ ] **Step 2: Add API functions**

```ts
export function ensureConversation(token: string, targetType: ConversationTargetType, targetId: string) {
  return api<EnsureConversationResponse>("/conversations/ensure", {
    method: "POST",
    body: JSON.stringify({ target_type: targetType, target_id: targetId })
  }, token);
}

export function conversationMessages(token: string, conversationId: string) {
  return api<MessagesResponse>(`/conversations/${conversationId}/messages`, {}, token);
}

export function sendConversationMessage(token: string, conversationId: string, content: string, contentType: MessageContentType = "text") {
  return api<SendMessageResponse>(`/conversations/${conversationId}/messages`, {
    method: "POST",
    body: JSON.stringify({ content, content_type: contentType })
  }, token);
}
```

- [ ] **Step 3: Typecheck**

Run:

```bash
npm run test -w apps/web
```

Expected: PASS.

### Task 10: Replace local session/message arrays

**Files:**
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/web/src/pages/App.tsx`

- [ ] **Step 1: Remove durable local state**

Remove `sessionItems`, `messages`, and `openClawMessages` as long-lived sources of truth.

- [ ] **Step 2: Use `conversationsQuery` for session list**

Session list renders `conversationsQuery.data.items`.

- [ ] **Step 3: Use selected conversation state**

Keep:

```ts
const [selected, setSelected] = useState<SelectedTarget>({ type: "guide" });
```

Where selected can be a profile target or `{ type: "conversation"; conversation }`.

- [ ] **Step 4: Fetch active messages**

When selected conversation exists, call `conversationMessages(token, conversation.id)`.

- [ ] **Step 5: Ensure from profile**

Profile "发送消息" calls `ensureConversation`, invalidates conversations, selects returned conversation.

- [ ] **Step 6: Build passes**

Run:

```bash
npm run test -w apps/web
```

Expected: PASS.

- [ ] **Step 7: Browser QA checkpoint**

With dev server running, verify:

- fresh login shows `暂无会话`;
- address book item click shows profile only;
- profile `发送消息` creates/selects a conversation;
- browser refresh keeps the conversation in the session list.

### Task 11: Implement unified send UX

**Files:**
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/web/src/pages/App.tsx`

- [ ] **Step 1: Send through unified endpoint**

Replace default BOT command send and OpenClaw send with `sendConversationMessage`.

- [ ] **Step 2: Keep optimistic UX**

On mutate:

- append temporary user message to current view;
- clear input immediately.

On success:

- merge returned persisted messages, dedupe by `id`;
- invalidate `["conversations"]`;
- invalidate or patch `["messages", conversation.id]`.

On error:

- append a local failure bubble only if backend did not return persisted system message.

- [ ] **Step 3: Verify manually in browser or with build**

Run:

```bash
npm run build -w apps/web
```

Expected: PASS.

- [ ] **Step 4: Browser QA checkpoint**

Verify:

- sending clears input immediately;
- user bubble appears before BOT/employee response;
- refresh restores persisted messages;
- default BOT `/help` and OpenClaw employee assistant both use the same message input.

### Task 12: Add frontend employee WebSocket client

**Files:**
- Create: `/Users/baiyu/workspaces/gitlab/openim/apps/web/src/api/wsClient.ts`
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/web/src/pages/App.tsx`

- [ ] **Step 1: Create WebSocket client**

Implement connect/reconnect with 1s to 15s backoff. Build URL only from explicit WebSocket base config:

```ts
const wsBaseUrl = import.meta.env.VITE_WS_BASE_URL || "ws://localhost:8080";
const wsUrl = `${wsBaseUrl}/ws?token=${encodeURIComponent(token)}`;
```

Use `import.meta.env.VITE_WS_BASE_URL || "ws://localhost:8080"` for local development, then append `/ws?token=<encoded access token>`. Do not rely on Vite HTTP proxy for WebSocket in P0.

- [ ] **Step 2: Handle events**

On `message.new`, patch active messages if open; otherwise invalidate. On `conversation.updated`, patch/invalidate conversations.

- [ ] **Step 3: Auth expiry**

On auth error/close caused by auth failure, clear auth and return to login.

- [ ] **Step 4: Verify typecheck**

Run:

```bash
npm run test -w apps/web
```

Expected: PASS.

- [ ] **Step 5: Browser QA checkpoint**

Open two browser contexts. Keep receiver online and send an employee message from sender. Verify receiver conversation list updates without refresh; then refresh receiver and verify the same message remains.

---

## Chunk 4: Integration Verification

### Task 13: Update compatibility tests and run backend suite

**Files:**
- Modify: `/Users/baiyu/workspaces/gitlab/openim/apps/server/tests/test_p0_flow.py`

- [ ] **Step 1: Update old tests**

Old tests expecting default conversation on `GET /api/conversations` must now expect no conversations until `ensure`.

- [ ] **Step 2: Run backend suite**

```bash
cd /Users/baiyu/workspaces/gitlab/openim/apps/server
uv run pytest -q
uv run ruff check .
```

Expected: all pass.

### Task 14: Run full frontend and plugin checks

**Files:** none expected.

- [ ] **Step 1: Run builds**

```bash
cd /Users/baiyu/workspaces/gitlab/openim
npm run build -w packages/openclaw-bot-plugin
npm run test -w apps/web
npm run build -w apps/web
```

Expected: all pass.

### Task 15: Manual end-to-end verification

**Files:** none expected.

- [ ] **Step 1: Start services**

```bash
cd /Users/baiyu/workspaces/gitlab/openim/apps/server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080
```

```bash
cd /Users/baiyu/workspaces/gitlab/openim
npm run dev -w apps/web -- --host 127.0.0.1 --port 5173
```

- [ ] **Step 2: Verify default BOT persistence**

In browser: create/ensure default BOT conversation, send `/help`, refresh, verify conversation and messages remain.

- [ ] **Step 3: Verify OpenClaw persistence**

Start local bridge, open OpenClaw assistant conversation, send message, refresh, verify conversation and messages remain.

- [ ] **Step 4: Create accepted friendship for manual employee realtime**

Use a one-off local command after creating/logging test users if the UI still lacks friend acceptance:

```bash
cd /Users/baiyu/workspaces/gitlab/openim/apps/server
uv run python - <<'PY'
from app.db.session import SessionLocal
from app.models.friendship import Friendship
from app.models.user import User

alice_username = "alice_manual"
bob_username = "bob_manual"

with SessionLocal() as db:
    alice = db.query(User).filter(User.username == alice_username).one()
    bob = db.query(User).filter(User.username == bob_username).one()
    existing = db.query(Friendship).filter(
        ((Friendship.requester_id == alice.id) & (Friendship.addressee_id == bob.id)) |
        ((Friendship.requester_id == bob.id) & (Friendship.addressee_id == alice.id))
    ).one_or_none()
    if existing:
        existing.status = "accepted"
    else:
        db.add(Friendship(requester_id=alice.id, addressee_id=bob.id, status="accepted"))
    db.commit()
PY
```

- [ ] **Step 5: Verify employee realtime**

Login two users in two browser contexts, create accepted friendship in DB/test setup, send A->B, verify B receives message while online and sees it after refresh.

### Task 15.5: Add Node smoke script for persistence contracts

**Files:**
- Create: `/Users/baiyu/workspaces/gitlab/openim/scripts/e2e-conversations.mjs`

- [ ] **Step 1: Add script**

The script should:

- register/login two users with timestamped usernames;
- ensure default BOT conversation;
- send `/help`;
- fetch messages and assert history contains `/help`;
- fetch messages and assert history contains the default BOT reply.
- This script does not cover employee friendship/realtime because P0 has no friend acceptance API; employee realtime is covered by pytest and browser QA. Do not add admin APIs only for this script.

- [ ] **Step 2: Run script**

```bash
cd /Users/baiyu/workspaces/gitlab/openim
node scripts/e2e-conversations.mjs
```

Expected: prints `conversation persistence smoke passed`.

### Task 16: Commit implementation

**Files:** all changed implementation files.

- [ ] **Step 1: Review diff**

```bash
git diff --stat
git diff -- apps/server apps/web packages scripts docs
```

- [ ] **Step 2: Commit**

```bash
git add apps/server apps/web scripts/e2e-conversations.mjs docs/superpowers/plans/2026-05-26-unified-conversations-messages.md
git commit -m "feat: persist unified conversations and messages"
```

Expected: implementation committed separately from the approved spec commit.
