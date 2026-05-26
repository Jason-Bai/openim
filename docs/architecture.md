# OpenIM Architecture

当前项目是一个面向员工的 IM 原型，核心目标是把员工账号、默认 BOT、OpenClaw 员工助手 BOT、真人员工会话统一到同一套会话和消息模型里。

```text
┌───────────────────────────────┐
│ apps/web                       │
│ React + Vite                   │
│                               │
│ - 通讯录 / 会话 / 聊天界面       │
│ - 员工 WebSocket /ws           │
└───────────────┬───────────────┘
                │ REST + WebSocket
                ▼
┌───────────────────────────────────────────────────────────┐
│ apps/server                                                │
│ FastAPI                                                    │
│                                                           │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│ │ Auth API     │  │ Users/Friends│  │ Conversations API│ │
│ └──────────────┘  └──────────────┘  └──────────────────┘ │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│ │ Bots API     │  │ Messages     │  │ Default BOT       │ │
│ └──────────────┘  └──────┬───────┘  └──────────────────┘ │
│ ┌──────────────────┐     │        ┌─────────────────────┐ │
│ │ Employee WS      │◄────┘        │ BOT Gateway          │ │
│ │ /ws              │              │ /bot-gateway/ws      │ │
│ └──────────────────┘              └──────────┬──────────┘ │
└───────────────┬──────────────────────────────┼────────────┘
                │                              │
                ▼                              ▼
┌───────────────────────────────┐   ┌───────────────────────────────┐
│ Local Data                     │   │ packages/openclaw-bot-plugin   │
│                               │   │ @openim/openclaw-bot-plugin    │
│ - SQLite dev DB                │   │                               │
│ - MySQL target                 │   │ scripts/openclaw-local-bridge  │
│ - Redis target for runtime     │   └───────────────┬───────────────┘
└───────────────────────────────┘                   │
                                                    ▼
                                      ┌───────────────────────────────┐
                                      │ Local OpenClaw                 │
                                      │                               │
                                      │ - OpenClaw Agent               │
                                      │ - OpenClaw Gateway             │
                                      └───────────────────────────────┘
```

## Module Responsibilities

- `apps/web`: Web UI. Shows contacts, conversations, profiles, and chat. Conversation and message state must come from backend APIs, not local-only state.
- `apps/server`: FastAPI backend. Owns auth, users, friendships, bots, conversations, messages, employee WebSocket, and BOT Gateway.
- `packages/openclaw-bot-plugin`: npm package used by external BOTs to connect to OpenIM BOT Gateway.
- `scripts/openclaw-local-bridge.mjs`: local bridge that binds one OpenIM BOT slot to the local OpenClaw agent for manual/E2E testing.
- `docs/*-plan.md`: product and technical plans. Keep implementation decisions aligned with these documents unless the user changes direction.

## Current P0 Runtime Flow

1. Employee logs in to OpenIM Web.
2. Employee opens default BOT from contacts and creates or connects an OpenClaw BOT slot.
3. Bridge/plugin connects to `/bot-gateway/ws` with `bot_id + token`.
4. Employee opens the OpenClaw BOT conversation.
5. Messages are persisted in `conversations/messages`.
6. Backend forwards OpenClaw BOT messages to BOT Gateway and stores the BOT reply.
7. Employee-to-employee messages create sender and receiver conversation copies and push receiver events through `/ws`.

## Development Defaults

- Backend dev URL: `http://127.0.0.1:8080`
- Frontend dev URL: `http://127.0.0.1:5173`
- Dev database: `apps/server/openim.db`
- Plugin package name: `@openim/openclaw-bot-plugin`
