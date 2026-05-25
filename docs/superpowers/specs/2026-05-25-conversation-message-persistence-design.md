# Unified Conversations And Messages Design

> Status: design draft for P0 implementation.

## Background

OpenIM currently has the key P0 flows running: employee login, default BOT commands, OpenClaw employee assistant connection through the plugin, and a real bridge from OpenIM to the local OpenClaw runtime. The remaining product gap is that conversations and messages are still held mostly in frontend memory. Refreshing the browser loses the left-side conversation list and the visible chat history.

This is not a frontend-only bug. It means the IM foundation is incomplete. Conversations and messages must become durable backend objects, and the frontend should render server state instead of inventing long-lived session state locally.

## Goals

- Persist conversations across refresh, backend restart, and browser session changes.
- Persist messages for default BOT, OpenClaw employee assistant BOT, and real employee contacts.
- Use one conversation/message model for all chat targets.
- Keep the existing contact-first interaction:
  - click contact or AI in address book;
  - show profile on the right;
  - click "发送消息";
  - create or restore the conversation;
  - enter the conversation view.
- Support minimum real-time push for employee-to-employee messages.
- Preserve fast chat UX: user messages appear immediately, input clears immediately, backend persistence reconciles afterward.

## Non-Goals

- No group chat in this phase.
- No read receipts.
- No typing indicators.
- No message recall/edit.
- No attachment/file messages.
- No multi-device delivery guarantees beyond best-effort WebSocket push plus persisted history.
- No offline notification. Offline users recover messages by loading conversations/history.

## Core Model

All chatable objects are represented as a `Conversation` target:

```text
system_default_bot -> the system default BOT
openclaw_bot       -> the employee's OpenClaw assistant BOT
user               -> a real employee account
```

The frontend does not create durable session rows in memory. It asks the backend to create or return the correct conversation.

## Data Model

### conversations

```text
id                  string primary key, conv_ + ULID
conversation_type   direct
owner_user_id       users.id
target_type         system_default_bot / openclaw_bot / user
target_id           default_bot / bot_id / user_id
title               denormalized display title
last_message_id     nullable messages.id
last_message_at     nullable datetime
created_at          datetime
updated_at          datetime
```

Constraint:

```text
unique(owner_user_id, target_type, target_id)
```

Indexes:

```text
idx_conversations_owner_sort(owner_user_id, last_message_at, updated_at)
idx_conversations_owner_target(owner_user_id, target_type, target_id) unique
```

Sorting:

```text
ORDER BY COALESCE(last_message_at, updated_at) DESC
```

### messages

```text
id                  string primary key, msg_ + ULID
conversation_id     conversations.id
client_message_id   nullable string, shared by mirrored employee DM rows
sender_type         user / bot / system
sender_id           user_id / bot_id / system_default_bot
content_type        text / code
content             text
status              sent / failed
created_at          datetime
```

P0 supports only `content_type = text` and `code` because default BOT `/connect` already returns code blocks.

Indexes:

```text
idx_messages_conversation_created(conversation_id, created_at, id)
```

Foreign keys:

```text
messages.conversation_id -> conversations.id ON DELETE CASCADE
conversations.last_message_id -> messages.id nullable, ON DELETE SET NULL
```

## Conversation Creation Rules

Registration and login do not create default BOT conversations.

BOT Gateway handshake does not create OpenClaw BOT conversations. Handshake only updates bot binding and connection state.

The only durable conversation creation path is:

```http
POST /api/conversations/ensure
```

Request:

```json
{
  "target_type": "openclaw_bot",
  "target_id": "bot_01..."
}
```

Rules:

- `system_default_bot`: allowed for every authenticated user with `target_id = default_bot`.
- `openclaw_bot`: allowed only when the bot belongs to or is actively bound to the current user.
- `user`: allowed only when the target user is already a friend of the current user. Non-friends return `FORBIDDEN`. The current user's own profile is not chatable and returns `FORBIDDEN`.

When a conversation is created for the first time, the backend inserts one initial message when useful:

- default BOT: `你好！输入 /help 查看可用命令。`
- OpenClaw BOT: `OpenClaw 员工助手已接入。你可以在这里开始对话。`
- user: no initial message.

## REST API

### List Conversations

```http
GET /api/conversations
```

Returns conversations owned by the current user.

Response item:

```json
{
  "id": "conv_01...",
  "conversation_type": "direct",
  "target_type": "openclaw_bot",
  "target_id": "bot_01...",
  "title": "OpenClaw 员工助手",
  "last_message": "hello",
  "last_message_id": "msg_01...",
  "last_message_at": "2026-05-25T15:00:00Z",
  "online": true
}
```

### Ensure Conversation

```http
POST /api/conversations/ensure
```

Returns an existing or newly created conversation.

Request:

```json
{
  "target_type": "system_default_bot",
  "target_id": "default_bot"
}
```

Response:

```json
{
  "ok": true,
  "data": {
    "conversation": {
      "id": "conv_01...",
      "conversation_type": "direct",
      "target_type": "system_default_bot",
      "target_id": "default_bot",
      "title": "默认 BOT",
      "last_message": "你好！输入 /help 查看可用命令。",
      "last_message_id": "msg_01...",
      "last_message_at": "2026-05-25T15:00:00Z",
      "online": true
    },
    "created": true,
    "initial_messages": [
      {
        "id": "msg_01...",
        "conversation_id": "conv_01...",
        "sender_type": "bot",
        "sender_id": "system_default_bot",
        "content_type": "text",
        "content": "你好！输入 /help 查看可用命令。",
        "status": "sent",
        "created_at": "2026-05-25T15:00:00Z"
      }
    ]
  },
  "request_id": "req_01..."
}
```

For existing conversations, `created` is `false` and `initial_messages` is an empty array.

### List Messages

```http
GET /api/conversations/{conversation_id}/messages?limit=50&before=msg_01...
```

P0 implementation returns the latest 50 messages by default. `limit` is capped at 100. Results are returned oldest-to-newest for display.

Response:

```json
{
  "ok": true,
  "data": {
    "items": [
      {
        "id": "msg_01...",
        "conversation_id": "conv_01...",
        "sender_type": "user",
        "sender_id": "123",
        "content_type": "text",
        "content": "hello",
        "status": "sent",
        "created_at": "2026-05-25T15:00:00Z"
      }
    ],
    "has_more": false,
    "next_before": null
  },
  "request_id": "req_01..."
}
```

### Send Message

```http
POST /api/conversations/{conversation_id}/messages
```

Request:

```json
{
  "content": "hello",
  "content_type": "text"
}
```

The backend loads the conversation and dispatches based on `target_type`.

Validation:

- `content_type` must be `text` or `code`; unsupported values return `VALIDATION_FAILED`.
- `content` is trimmed for validation and must contain at least one non-whitespace character.
- `content` max length is 4000 characters.
- The persisted content keeps the submitted text after trimming leading/trailing whitespace.

Response:

```json
{
  "ok": true,
  "data": {
    "conversation": {
      "id": "conv_01...",
      "last_message": "OpenClaw reply",
      "last_message_id": "msg_03...",
      "last_message_at": "2026-05-25T15:00:03Z"
    },
    "messages": [
      {
        "id": "msg_02...",
        "conversation_id": "conv_01...",
        "sender_type": "user",
        "sender_id": "123",
        "content_type": "text",
        "content": "hello",
        "status": "sent",
        "created_at": "2026-05-25T15:00:00Z"
      },
      {
        "id": "msg_03...",
        "conversation_id": "conv_01...",
        "sender_type": "bot",
        "sender_id": "bot_01...",
        "content_type": "text",
        "content": "OpenClaw reply",
        "status": "sent",
        "created_at": "2026-05-25T15:00:03Z"
      }
    ]
  },
  "request_id": "req_01..."
}
```

For employee-to-employee sends, `messages` contains the sender-side persisted message. The receiver-side copy is delivered through WebSocket when the receiver is online and is available through the receiver's own history API.

## Delivery Rules

### system_default_bot

Flow:

1. Persist the user command as a `user` message.
2. Route content to `default-bot-service`.
3. Persist the default BOT reply as `bot` message.
4. Update conversation last message fields.
5. Return `data.conversation` plus `data.messages` containing the persisted user command and persisted BOT reply.

The existing `POST /api/default-bot/commands` remains as a backend compatibility endpoint during this migration, but the frontend must stop using it. New frontend sends default BOT commands through `POST /api/conversations/{conversation_id}/messages`.

### openclaw_bot

Flow:

1. Verify current user owns or is bound to the bot.
2. Persist the user message.
3. Send an `inbound_message` through BOT Gateway.
4. Wait for plugin `send_message` response.
5. Persist OpenClaw reply as `bot` message.
6. Update conversation last message fields.
7. Return persisted reply.

If OpenClaw times out or is disconnected:

- The user message remains persisted.
- The backend appends a `system` message explaining the failure.
- The API returns HTTP `200` with `ok: true` and includes both the persisted user message and persisted system failure message in `data.messages`.
- The system failure message uses `sender_type = system`, `sender_id = system`, `status = sent`, and content `OpenClaw 员工助手暂时没有返回，请稍后重试。`
- `conversation.last_message_id` points to the system failure message.

### user

Flow for A sending to B:

1. Verify A and B are friends.
2. Persist message in A's conversation with B.
3. Ensure B's reverse conversation with A.
4. Persist corresponding message in B's conversation.
5. Update both conversations' last message fields.
6. If B has an active employee WebSocket session, push `message.new` and `conversation.updated`.
7. If B is offline, do nothing else; B recovers via persisted history.

All seven steps run inside one database transaction except WebSocket push. If database persistence succeeds but WebSocket push fails, the API still returns success because the receiver can recover by refetching history. Both persisted message rows use the same `client_message_id`, `content`, `content_type`, `status`, and `created_at`.

Friendship integration:

- Use the existing `friendships` table as the source of truth.
- A and B are friends only when a row exists for the pair in either direction with `status = accepted`.
- This phase does not add friend acceptance UI or APIs. If no accepted relationship exists, `ensure` and send return `FORBIDDEN`.

## Employee WebSocket

Endpoint:

```text
/ws
```

Auth:

- JWT passed as `token` query parameter: `ws://localhost:8080/ws?token=<access_token>`.
- Invalid or expired token closes the socket and frontend returns to login.

Session manager:

```text
user_id -> set[WebSocket]
```

Events:

```json
{
  "type": "message.new",
  "conversation_id": "conv_01...",
  "message": {
    "id": "msg_01...",
    "sender_type": "user",
    "sender_id": "123",
    "content_type": "text",
    "content": "hello",
    "status": "sent",
    "created_at": "2026-05-25T15:00:00Z"
  }
}
```

```json
{
  "type": "conversation.updated",
  "conversation": {
    "id": "conv_01...",
    "last_message": "hello",
    "last_message_id": "msg_01...",
    "last_message_at": "2026-05-25T15:00:00Z"
  }
}
```

```json
{
  "type": "error",
  "error": {
    "code": "AUTH_EXPIRED",
    "message": "登录已过期",
    "retryable": false
  }
}
```

Frontend reconnect:

- Exponential backoff from 1s to 15s.
- On reconnect, refetch conversations and current conversation messages.

Connected event handling:

- `message.new`: if the pushed `conversation_id` is currently open, append the message to the active messages query when it is not already present; otherwise invalidate `["messages", conversation_id]`. Always patch or invalidate `["conversations"]` so the left list updates.
- `conversation.updated`: patch the matching conversation in `["conversations"]` when present; otherwise invalidate `["conversations"]`.
- Unknown event types are ignored and logged to console in development.

## Frontend State

Remove long-lived local arrays for:

- `sessionItems`
- default BOT `messages`
- OpenClaw `openClawMessages`

Keep local state only for:

- selected `conversation_id` or selected contact profile;
- current input text;
- temporary optimistic message IDs while a send request is pending.

TanStack Query owns:

- conversation list;
- current conversation messages;
- contacts;
- bots.

Interaction flow:

```text
Address book item click
  -> show profile, no conversation mutation

Profile "发送消息"
  -> POST /api/conversations/ensure
  -> refetch conversations
  -> select returned conversation
  -> GET messages

Conversation item click
  -> select conversation
  -> GET messages

Send message
  -> optimistic append user message
  -> clear input
  -> POST /api/conversations/{id}/messages
  -> reconcile/refetch messages and conversations
```

## Error Handling

- `FORBIDDEN`: user is not allowed to create or send to the target.
- `CONVERSATION_NOT_FOUND`: conversation does not belong to current user.
- `MESSAGE_DELIVERY_FAILED`: reserved for non-OpenClaw delivery failures where no target-specific success-with-system-message contract exists. For OpenClaw disconnected or timeout cases, the send API returns HTTP `200` with persisted user and system messages.
- `VALIDATION_FAILED`: unsupported `content_type`, empty/whitespace-only content, or content longer than 4000 characters.
- `AUTH_EXPIRED`: frontend clears login state.

The UI should prefer persisted system messages over ephemeral toast-only errors for send failures.

## Testing

Backend tests:

- `ensure` does not create duplicates for the same owner/target.
- registration/login no longer auto-create default BOT conversation.
- default BOT conversation is created only by `ensure`.
- OpenClaw handshake does not create a conversation.
- default BOT command messages persist and survive reload.
- OpenClaw BOT user message and reply persist.
- OpenClaw disconnected/timeout persists the user message plus system failure message and returns `ok: true`.
- employee-to-employee message creates sender and receiver conversation rows.
- offline receiver sees message after fetching conversations/messages.
- online receiver receives `message.new`.

Frontend tests/build verification:

- conversation list renders from backend conversations.
- address book click shows profile only.
- profile "发送消息" calls ensure and switches to conversation view.
- refresh after conversation creation restores left-side conversation list.
- refresh after messages restores chat history.
- sending clears input immediately and displays optimistic user message.

Manual verification:

- Create/login employee A.
- Connect local OpenClaw assistant.
- Start OpenClaw conversation, send message, refresh, verify conversation and messages remain.
- Start default BOT conversation, run `/help`, refresh, verify history remains.
- Login employee B in another browser, add friendship, send A->B, verify B receives realtime message when online.

## Migration From Current Code

Current code creates default BOT conversations in registration/login and in `list_conversations`. This must be removed.

Current code creates OpenClaw BOT conversation during handshake. This must be removed.

Existing local development rows with `target_type = bot` are migrated in-place to `target_type = openclaw_bot` and `conversation_type = direct`. There is no production data migration requirement yet because this project has not been deployed. The Alembic migration includes the local remap so current manual test data remains usable.

Current frontend stores `sessionItems`, `messages`, and `openClawMessages` in component state. These must be replaced by conversation/message queries and short-lived optimistic entries.

Existing compatibility endpoints remain during migration for old tests and manual fallback, but the frontend must use the unified conversation message API.
