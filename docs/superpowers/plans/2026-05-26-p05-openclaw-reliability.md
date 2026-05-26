# P0.5 OpenClaw Assistant Reliability Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the connected OpenClaw employee-assistant BOT trustworthy, diagnosable, and stable enough for repeated manual demos and early internal trials.

**Architecture:** Keep the current FastAPI + React + npm Plugin architecture. Add a backend status event path from BOT Gateway state changes to employee WebSocket sessions, add a lightweight default-BOT diagnostic command, and tighten frontend behavior around connection state, message failure, and contact/session navigation. Avoid new product surfaces unless they directly support the OpenClaw assistant reliability loop.

**Tech Stack:** FastAPI, SQLAlchemy, FastAPI WebSocket, pytest, React, TypeScript, TanStack Query, Ant Design, `@openim/openclaw-bot-plugin`, local SQLite dev DB.

---

## Scope

P0.5 includes:

- Real-time `bot.status_changed` updates for the current employee.
- Clear OpenClaw assistant message behavior for connected, disconnected, timeout, and backend-restart cases.
- `/diagnose {bot_id}` in the default BOT.
- Finalized contact/session behavior for default BOT, OpenClaw BOT, and employee self/profile entries.
- A repeatable local demo verification script that checks the main P0.5 flow.

P0.5 does not include:

- Friend request accept/reject UI.
- Full BOT management UI.
- Group chat, zones, files, read receipts, message search, or admin pages.
- Public npm publishing.
- Multi-instance Redis-backed presence. This plan stays single-process/dev focused but leaves interfaces compatible with Redis later.

---

## File Map

Backend:

- Modify `apps/server/app/ws/employee.py`: expose safe broadcast helpers and tolerate disconnected sockets.
- Modify `apps/server/app/ws/bot_gateway.py`: emit bot status events on handshake, disconnect, auth failure where useful.
- Modify `apps/server/app/services/bots.py`: centralize bot serialization/status mutation helpers and add diagnostic data lookup.
- Modify `apps/server/app/services/default_bot.py`: add `/diagnose {bot_id}` command and update `/help` text.
- Modify `apps/server/app/services/messages.py`: preserve current immediate user-message persistence and make OpenClaw failure messaging deterministic.
- Modify `apps/server/app/core/errors.py`: add or reuse precise error codes only when tests prove current codes are ambiguous.
- Modify `apps/server/tests/test_p0_flow.py`: cover P0.5 status events, diagnose command, and message failure behavior.

Frontend:

- Modify `apps/web/src/api/openim.ts`: add any missing payload types for `bot.status_changed` and diagnostic-friendly fields if needed.
- Modify `apps/web/src/pages/App.tsx`: handle `bot.status_changed`, update contacts/conversations cache, stabilize profile/session behavior, and improve OpenClaw failure UX.
- Modify `apps/web/src/styles.css`: only minimal styles for status/notice/retry if needed.

Plugin / local tooling:

- Modify `scripts/e2e-p0.mjs` or create `scripts/e2e-p05.mjs`: verify login, contacts, connected OpenClaw BOT, backend restart expectation where feasible.
- Modify `package.json`: add `e2e:p05` script if creating a new script.
- Modify `README.md`: document P0.5 local run and verification commands.

---

## Chunk 1: Real-Time BOT Status Events

### Task 1: Backend status event contract

**Files:**

- Modify: `apps/server/tests/test_p0_flow.py`
- Modify: `apps/server/app/ws/employee.py`
- Modify: `apps/server/app/ws/bot_gateway.py`
- Modify: `apps/server/app/services/bots.py`

- [ ] **Step 1: Write the failing test for status event payload shape**

Add a test near the existing BOT Gateway tests:

```python
def test_bot_gateway_pushes_status_changed_to_owner(client: TestClient) -> None:
    user_id, token = register_user(client, "zhangsan", "E001", "张三")
    bot_id = re.search(r"BOT_ID: (bot_[A-Z0-9]+)", command(client, token, "/new-bot")["content"]).group(1)
    payload = json.loads(command(client, token, f"/connect {bot_id}")["content"])

    with client.websocket_connect(f"/ws?token={token}") as employee_ws:
        with client.websocket_connect("/bot-gateway/ws") as bot_ws:
            bot_ws.send_json({
                "type": "auth",
                "request_id": "req_auth",
                "protocol_version": "bot-v1",
                "bot_id": bot_id,
                "token": payload["token"],
            })
            assert bot_ws.receive_json()["ok"] is True
            bot_ws.send_json({
                "type": "handshake",
                "request_id": "req_handshake",
                "protocol_version": "bot-v1",
                "bot_id": bot_id,
                "runtime": {"name": "test", "version": "0.1.0"},
            })
            assert bot_ws.receive_json()["ok"] is True
            event = employee_ws.receive_json()
            assert event["type"] == "bot.status_changed"
            assert event["bot"]["bot_id"] == bot_id
            assert event["bot"]["connect_status"] == "connected"
            assert event["bot"]["binding_status"] == "active"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd apps/server && uv run pytest tests/test_p0_flow.py::test_bot_gateway_pushes_status_changed_to_owner -q
```

Expected: fail because no `bot.status_changed` event is sent.

- [ ] **Step 3: Add a safe employee WebSocket send helper**

In `apps/server/app/ws/employee.py`, update `send_to_user` so stale sockets are removed instead of crashing future sends:

```python
    async def send_to_user(self, user_id: int, payload: dict[str, object]) -> None:
        sockets = list(self._sessions.get(user_id, set()))
        stale: list[WebSocket] = []
        for websocket in sockets:
            try:
                await websocket.send_json(payload)
            except Exception:
                stale.append(websocket)
        for websocket in stale:
            self.unregister(user_id, websocket)
```

- [ ] **Step 4: Add bot serialization for status events**

In `apps/server/app/services/bots.py`, add:

```python
def serialize_bot_for_owner(db: Session, bot: Bot) -> dict[str, object]:
    binding = db.scalar(
        select(UserBotBinding).where(
            UserBotBinding.user_id == bot.owner_user_id,
            UserBotBinding.bot_id == bot.bot_id,
            UserBotBinding.status == "active",
        )
    )
    return {
        "bot_id": bot.bot_id,
        "name": bot.name,
        "bot_type": bot.bot_type,
        "connect_status": bot.connect_status,
        "binding_status": binding.status if binding else "none",
        "last_seen_at": utc_iso(bot.last_seen_at),
        "first_connected_at": utc_iso(bot.first_connected_at),
    }
```

Then make `list_user_bots()` call this helper to avoid divergent payloads.

- [ ] **Step 5: Emit status event on successful handshake**

In `apps/server/app/ws/bot_gateway.py`, after `mark_handshake(...)` and `db.commit()`, send:

```python
from app.services.bots import serialize_bot_for_owner
from app.ws.employee import employee_ws_sessions

await employee_ws_sessions.send_to_user(
    bot.owner_user_id,
    {"type": "bot.status_changed", "bot": serialize_bot_for_owner(db, bot)},
)
```

Keep this after commit so frontend refreshes can also read the updated state through REST.

- [ ] **Step 6: Run test to verify it passes**

Run:

```bash
cd apps/server && uv run pytest tests/test_p0_flow.py::test_bot_gateway_pushes_status_changed_to_owner -q
```

Expected: pass.

- [ ] **Step 7: Add disconnect status event test**

Add:

```python
def test_bot_gateway_pushes_disconnected_on_socket_close(client: TestClient) -> None:
    token = register_and_login(client)
    bot_id = re.search(r"BOT_ID: (bot_[A-Z0-9]+)", command(client, token, "/new-bot")["content"]).group(1)
    payload = json.loads(command(client, token, f"/connect {bot_id}")["content"])

    with client.websocket_connect(f"/ws?token={token}") as employee_ws:
        with client.websocket_connect("/bot-gateway/ws") as bot_ws:
            bot_ws.send_json({"type": "auth", "request_id": "a", "protocol_version": "bot-v1", "bot_id": bot_id, "token": payload["token"]})
            bot_ws.receive_json()
            bot_ws.send_json({"type": "handshake", "request_id": "h", "protocol_version": "bot-v1", "bot_id": bot_id, "runtime": {}})
            bot_ws.receive_json()
            assert employee_ws.receive_json()["bot"]["connect_status"] == "connected"
        event = employee_ws.receive_json()
        assert event["type"] == "bot.status_changed"
        assert event["bot"]["connect_status"] == "disconnected"
```

- [ ] **Step 8: Implement disconnect event**

In `bot_gateway.py` `finally`, after setting `bot.connect_status = "disconnected"` and committing, send the same event to `bot.owner_user_id`. Guard send in a broad `try/except` because shutdown paths should not mask DB cleanup.

- [ ] **Step 9: Run targeted and full backend tests**

Run:

```bash
cd apps/server && uv run pytest tests/test_p0_flow.py::test_bot_gateway_pushes_status_changed_to_owner tests/test_p0_flow.py::test_bot_gateway_pushes_disconnected_on_socket_close -q
cd apps/server && uv run pytest -q
```

Expected: all pass.

- [ ] **Step 10: Commit**

```bash
git add apps/server/app/ws/employee.py apps/server/app/ws/bot_gateway.py apps/server/app/services/bots.py apps/server/tests/test_p0_flow.py
git commit -m "feat: push bot status changes"
```

---

## Chunk 2: Frontend Status Synchronization

### Task 2: Consume `bot.status_changed` in the web app

**Files:**

- Modify: `apps/web/src/api/openim.ts`
- Modify: `apps/web/src/pages/App.tsx`
- Test: TypeScript build via `npm run test -w apps/web`

- [ ] **Step 1: Add the event type**

In `apps/web/src/api/openim.ts`, add:

```ts
export type BotStatusChangedEvent = {
  type: "bot.status_changed";
  bot: BotItem;
};
```

- [ ] **Step 2: Update WebSocket message parsing**

In `useEmployeeWebSocket`, extend the payload union:

```ts
const payload = JSON.parse(event.data) as {
  type: string;
  message?: ConversationMessage;
  conversation?: Conversation;
  bot?: BotItem;
};
```

- [ ] **Step 3: Update contacts cache on status event**

Add helper near existing cache helpers:

```ts
function updateContactBot(current: { ai: ContactItem[]; all: ContactItem[] }, bot: BotItem) {
  const update = (item: ContactItem): ContactItem =>
    item.contact_type === "openclaw_bot" && item.bot.bot_id === bot.bot_id
      ? { ...item, title: bot.name, subtitle: bot.bot_id, online: bot.connect_status === "connected", bot }
      : item;
  return { ai: current.ai.map(update), all: current.all.map(update) };
}
```

In `useEmployeeWebSocket`, handle:

```ts
if (payload.type === "bot.status_changed" && payload.bot) {
  queryClient.setQueryData<{ ai: ContactItem[]; all: ContactItem[] }>(["contacts"], (current) =>
    current ? updateContactBot(current, payload.bot!) : current
  );
  queryClient.invalidateQueries({ queryKey: ["contacts"] });
  queryClient.invalidateQueries({ queryKey: ["conversations"] });
}
```

- [ ] **Step 4: Ensure selected OpenClaw profile refreshes**

`resolveSelectedView` should already read from contacts. Verify the selected profile updates after cache change. If not, adjust dependencies to include `contactsQuery.data?.all` only.

- [ ] **Step 5: Run frontend type check**

```bash
npm run test -w apps/web
```

Expected: pass.

- [ ] **Step 6: Manual verification**

Run backend, web, and local bridge. In Chrome:

1. Open `http://127.0.0.1:5173`.
2. Log in as `qa_1779724360080`.
3. Confirm OpenClaw BOT shows green dot.
4. Stop bridge.
5. Confirm it changes offline after backend sends disconnect event.
6. Restart bridge.
7. Confirm it changes online without page refresh.

- [ ] **Step 7: Commit**

```bash
git add apps/web/src/api/openim.ts apps/web/src/pages/App.tsx
git commit -m "feat: sync bot status in web client"
```

---

## Chunk 3: Default BOT Diagnostics

### Task 3: Add `/diagnose {bot_id}`

**Files:**

- Modify: `apps/server/tests/test_p0_flow.py`
- Modify: `apps/server/app/services/default_bot.py`
- Modify: `apps/server/app/services/bots.py`

- [ ] **Step 1: Write failing tests**

Add tests:

```python
def test_default_bot_diagnose_connected_bot(client: TestClient) -> None:
    user_id, token = register_user(client, "zhangsan", "E001", "张三")
    bot_id = re.search(r"BOT_ID: (bot_[A-Z0-9]+)", command(client, token, "/new-bot")["content"]).group(1)
    mark_bot_connected(user_id, bot_id)

    reply = command(client, token, f"/diagnose {bot_id}")

    assert reply["reply_type"] == "text"
    assert f"BOT_ID: {bot_id}" in reply["content"]
    assert "连接状态: connected" in reply["content"]
    assert "绑定状态: active" in reply["content"]
    assert "建议: 可以开始对话" in reply["content"]


def test_default_bot_diagnose_requires_bot_id(client: TestClient) -> None:
    token = register_and_login(client)
    reply = command(client, token, "/diagnose")
    assert "请输入要诊断的 BOT ID" in reply["content"]
```

- [ ] **Step 2: Run tests to verify failure**

```bash
cd apps/server && uv run pytest tests/test_p0_flow.py::test_default_bot_diagnose_connected_bot tests/test_p0_flow.py::test_default_bot_diagnose_requires_bot_id -q
```

Expected: fail because command is unknown.

- [ ] **Step 3: Add diagnostic service function**

In `apps/server/app/services/bots.py`, add:

```python
def diagnose_bot(db: Session, user_id: int, bot_id: str) -> dict[str, object]:
    bot = get_owned_bot(db, user_id, bot_id)
    binding = db.scalar(
        select(UserBotBinding).where(
            UserBotBinding.user_id == user_id,
            UserBotBinding.bot_id == bot.bot_id,
            UserBotBinding.status == "active",
        )
    )
    last_log = db.scalar(
        select(BotConnectionLog)
        .where(BotConnectionLog.bot_id == bot.bot_id)
        .order_by(BotConnectionLog.created_at.desc(), BotConnectionLog.id.desc())
    )
    return {
        "bot_id": bot.bot_id,
        "name": bot.name,
        "connect_status": bot.connect_status,
        "binding_status": binding.status if binding else "none",
        "last_seen_at": utc_iso(bot.last_seen_at),
        "last_event_type": last_log.event_type if last_log else None,
        "last_error_code": last_log.error_code if last_log else None,
        "token_status": "revealed" if bot.token_revealed_at else "not_revealed",
    }
```

- [ ] **Step 4: Add command text**

In `default_bot.py`, import `diagnose_bot`, add `/diagnose {bot_id}` to `HELP_TEXT`, and handle:

```python
    if name == "/diagnose":
        if len(parts) < 2:
            return text_reply("请输入要诊断的 BOT ID：/diagnose {bot_id}")
        return text_reply(_format_diagnosis(diagnose_bot(db, user.id, parts[1])))
```

Add formatter:

```python
def _format_diagnosis(data: dict[str, object]) -> str:
    suggestion = "请先输入 /connect {bot_id} 获取连接信息并启动 OpenClaw 员工助手"
    if data["connect_status"] == "connected" and data["binding_status"] == "active":
        suggestion = "可以开始对话"
    elif data["connect_status"] in {"pending", "disconnected"}:
        suggestion = "请确认 OpenClaw 员工助手进程正在运行，并使用最新连接信息"
    return (
        f"BOT 诊断结果\n"
        f"BOT_ID: {data['bot_id']}\n"
        f"名称: {data['name']}\n"
        f"连接状态: {data['connect_status']}\n"
        f"绑定状态: {data['binding_status']}\n"
        f"最后在线: {data['last_seen_at'] or '无'}\n"
        f"最后事件: {data['last_event_type'] or '无'}\n"
        f"最后错误: {data['last_error_code'] or '无'}\n"
        f"Token 状态: {data['token_status']}\n"
        f"建议: {suggestion}"
    )
```

- [ ] **Step 5: Run targeted tests**

```bash
cd apps/server && uv run pytest tests/test_p0_flow.py::test_default_bot_diagnose_connected_bot tests/test_p0_flow.py::test_default_bot_diagnose_requires_bot_id -q
```

Expected: pass.

- [ ] **Step 6: Run full backend checks**

```bash
cd apps/server && uv run pytest -q
cd apps/server && uv run ruff check .
```

Expected: pass.

- [ ] **Step 7: Commit**

```bash
git add apps/server/app/services/bots.py apps/server/app/services/default_bot.py apps/server/tests/test_p0_flow.py
git commit -m "feat: add bot diagnosis command"
```

---

## Chunk 4: OpenClaw Message Failure and Retry UX

### Task 4: Make failure states explicit without inventing a new message protocol

**Files:**

- Modify: `apps/server/tests/test_p0_flow.py`
- Modify: `apps/server/app/services/messages.py`
- Modify: `apps/web/src/pages/App.tsx`
- Modify: `apps/web/src/styles.css` if needed

- [ ] **Step 1: Lock current backend behavior with tests**

Add or update tests so behavior is explicit:

```python
def test_openclaw_timeout_preserves_user_message_and_system_failure(client: TestClient, monkeypatch) -> None:
    user_id, token = register_user(client, "zhangsan", "E001", "张三")
    bot_id = re.search(r"BOT_ID: (bot_[A-Z0-9]+)", command(client, token, "/new-bot")["content"]).group(1)
    mark_bot_connected(user_id, bot_id)
    conversation = client.post(
        "/api/conversations/ensure",
        headers=auth_headers(token),
        json={"target_type": "openclaw_bot", "target_id": bot_id},
    ).json()["data"]["conversation"]

    async def fail_reply(**kwargs):
        raise ApiError("MESSAGE_SEND_FAILED", "等待 BOT 回复超时", retryable=True)

    monkeypatch.setattr("app.services.messages.bot_gateway_sessions.request_reply", fail_reply)

    response = client.post(
        f"/api/conversations/{conversation['id']}/messages",
        headers=auth_headers(token),
        json={"content": "hello", "content_type": "text"},
    )

    assert response.status_code == 200
    messages = response.json()["data"]["messages"]
    assert [item["sender_type"] for item in messages] == ["user", "system"]
    assert messages[0]["content"] == "hello"
    assert "暂时没有返回" in messages[1]["content"]
```

- [ ] **Step 2: Run test**

```bash
cd apps/server && uv run pytest tests/test_p0_flow.py::test_openclaw_timeout_preserves_user_message_and_system_failure -q
```

Expected: pass if current behavior already matches. If it fails, implement only the minimal change in `messages.py`.

- [ ] **Step 3: Frontend retry UX plan**

Keep P0.5 simple: do not add per-message retry storage. Add a small “重新发送” button only when the last visible message is a system failure in an OpenClaw conversation and the previous user message exists.

Implementation in `ConversationChat`:

- Derive `lastSystemFailure` from `messages`.
- Derive `lastUserMessage` from previous user message.
- Render a small button near `chatNotice` or under the system failure:

```tsx
{canRetryLastOpenClawMessage && (
  <Button size="small" onClick={() => onSubmit(lastUserMessage.content)} disabled={loading || disabled}>
    重新发送上一条
  </Button>
)}
```

- [ ] **Step 4: Run frontend type check**

```bash
npm run test -w apps/web
```

Expected: pass.

- [ ] **Step 5: Manual verification**

1. Stop bridge.
2. Open OpenClaw BOT conversation.
3. Confirm input is disabled with clear text.
4. Start bridge.
5. Send a message.
6. If OpenClaw fails/timeout occurs, confirm user message remains and failure message appears.
7. Click retry after bridge is healthy.

- [ ] **Step 6: Commit**

```bash
git add apps/server/app/services/messages.py apps/server/tests/test_p0_flow.py apps/web/src/pages/App.tsx apps/web/src/styles.css
git commit -m "feat: clarify openclaw message failure ux"
```

---

## Chunk 5: Contact / Session Interaction Finalization

### Task 5: Make navigation rules explicit and tested manually

**Files:**

- Modify: `apps/web/src/pages/App.tsx`
- Modify: `apps/web/src/styles.css`
- Modify: `README.md`

- [ ] **Step 1: Verify current rules in code**

Rules:

- Contact list click shows profile only.
- Profile “发送消息” calls `/api/conversations/ensure` and switches to sessions.
- Default BOT does not appear in sessions until the user opens it.
- Self profile never shows “发送消息”.
- OpenClaw BOT profile disables “发送消息” when disconnected.

- [ ] **Step 2: Fix any rule violations minimally**

Do not add new UI sections. Keep the existing three-column layout.

- [ ] **Step 3: Add README acceptance checklist**

In `README.md`, add a P0.5 manual checklist:

```markdown
## P0.5 Manual Acceptance

- [ ] 通讯录“已添加的 AI” shows 默认 BOT and OpenClaw 员工助手.
- [ ] 通讯录“全部联系人” shows 默认 BOT, OpenClaw 员工助手, and current employee.
- [ ] Clicking a contact opens profile, not a conversation.
- [ ] Clicking 发送消息 creates/opens the conversation.
- [ ] Default BOT appears in 会话 only after opening/sending.
- [ ] OpenClaw BOT status changes online/offline without refresh.
- [ ] OpenClaw BOT remains usable after backend restart and Plugin reconnect.
```

- [ ] **Step 4: Run frontend checks**

```bash
npm run test -w apps/web
npm run build -w apps/web
```

Expected: pass; Vite chunk warning is acceptable.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/pages/App.tsx apps/web/src/styles.css README.md
git commit -m "docs: add p05 interaction acceptance"
```

---

## Chunk 6: P0.5 E2E Demo Script

### Task 6: Add repeatable P0.5 smoke verification

**Files:**

- Create: `scripts/e2e-p05.mjs`
- Modify: `package.json`
- Modify: `README.md`

- [ ] **Step 1: Create script skeleton**

Create `scripts/e2e-p05.mjs` based on `scripts/e2e-p0.mjs`.

The script should:

1. Register or log in a unique test user.
2. Ensure default BOT conversation.
3. Run `/new-bot`.
4. Run `/connect {bot_id}` and parse JSON.
5. Connect Plugin directly using `OpenClawBotClient` with a test `onMessage` reply.
6. Ensure OpenClaw BOT conversation.
7. Send a message.
8. Assert the reply is persisted.
9. Fetch `/api/contacts` and assert `ai` and `all` both include default BOT and OpenClaw BOT.

- [ ] **Step 2: Add package script**

In root `package.json`:

```json
"e2e:p05": "npm run build -w packages/openclaw-bot-plugin && node scripts/e2e-p05.mjs"
```

- [ ] **Step 3: Run the script against local backend**

```bash
npm run e2e:p05
```

Expected: JSON output with `ok: true`, `contactsOk: true`, `messageOk: true`, `botConnected: true`.

- [ ] **Step 4: Document it**

In `README.md`, add:

```bash
npm run e2e:p05
```

and mention it requires backend on `127.0.0.1:8080`.

- [ ] **Step 5: Commit**

```bash
git add scripts/e2e-p05.mjs package.json README.md
git commit -m "test: add p05 e2e smoke"
```

---

## Final Verification

Run all checks:

```bash
cd apps/server && uv run pytest -q
cd apps/server && uv run ruff check .
npm run test -w apps/web
npm run build -w apps/web
npm run test -w packages/openclaw-bot-plugin
npm run build -w packages/openclaw-bot-plugin
npm run e2e:p05
```

Expected:

- Backend tests pass.
- Ruff passes.
- Frontend type check and build pass; Vite chunk warning is acceptable.
- Plugin type check and build pass.
- P0.5 smoke script returns success.

Manual browser checks:

1. Open `http://127.0.0.1:5173`.
2. Log in as the current QA user or a fresh test user.
3. Confirm contacts list includes default BOT, OpenClaw BOT, and employee in `全部联系人`.
4. Confirm clicking contact shows profile.
5. Confirm sending opens conversation.
6. Confirm OpenClaw BOT online/offline changes without refresh.
7. Restart backend while bridge stays running; confirm BOT reconnects and can chat.

---

## Rollback Notes

If P0.5 introduces regressions:

- Status push changes can be disabled by removing `employee_ws_sessions.send_to_user(...)` calls from `bot_gateway.py`; REST polling still works.
- `/diagnose` is isolated in `default_bot.py` and `bots.py`; removing the command does not affect existing `/connect` flow.
- Frontend status handling only updates React Query caches; invalidating `contacts` and `conversations` remains safe fallback behavior.
