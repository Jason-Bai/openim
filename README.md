# OpenIM

OpenIM is a lightweight internal IM prototype for connecting employee accounts with OpenClaw employee-assistant BOTs.

It provides a web chat UI, a FastAPI backend, a BOT Gateway WebSocket protocol, and an official Node.js plugin package for external/OpenClaw BOT runtimes.

中文文档: [README_zh.md](README_zh.md)

## Why OpenIM

OpenIM explores a simple operating model for employee assistants:

```text
employee account -> default BOT -> BOT slot -> OpenClaw plugin -> BOT Gateway -> conversation
```

The goal is to make BOT onboarding, connection state, contacts, conversations, and message history backend-backed and reproducible in local development.

## Features

- Employee registration and login.
- Default BOT for onboarding and BOT management.
- BOT slot creation with `/new-bot`.
- Connection info generation with `/connect {bot_id}`.
- BOT Gateway WebSocket auth, handshake, heartbeat, and reconnect support.
- Backend-backed conversations and message history.
- Contacts and chat UI for default BOTs, OpenClaw BOTs, and employees.
- Official BOT SDK package: `@openim/openclaw-bot-plugin`.

## Tech Stack

| Area | Stack |
|---|---|
| Web | React, Vite, TypeScript, TanStack Query, Zustand, Ant Design |
| Server | Python, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2.x, Alembic |
| Local data | SQLite |
| Planned services | MySQL, Redis |
| BOT SDK | TypeScript, Node.js 18+, WebSocket JSON, tsup |

## Project Structure

```text
openim/
  apps/
    web/                         # React web client
    server/                      # FastAPI backend
  packages/
    openclaw-bot-plugin/         # Official BOT SDK package
  scripts/                       # Local smoke and bridge scripts
  docs/                          # Architecture, product, workflow, and test docs
```

## Quick Start

Install dependencies:

```bash
npm install
cd apps/server && uv sync --dev
```

Start the backend:

```bash
cd apps/server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Start the web app in another terminal:

```bash
npm run dev -w apps/web
```

Open the app:

```text
http://127.0.0.1:5173
```

## Common Commands

Backend:

```bash
cd apps/server && uv run pytest -q
cd apps/server && uv run ruff check .
```

Frontend:

```bash
npm run test -w apps/web
npm run build -w apps/web
```

Smoke tests:

```bash
npm run e2e:p0
npm run e2e:p0:plugin
npm run e2e:p05
npm run e2e:openclaw:local
```

`e2e:p05` expects the backend to be running on `127.0.0.1:8080`.

The local OpenClaw bridge smoke test uses:

```text
OPENCLAW_CONTROL_URL=http://127.0.0.1:18789
```

## Development Workflow

Non-trivial work uses:

- GitHub Issues as work entries.
- Per-requirement delivery registry files.
- Isolated branches and worktrees.
- Pull Requests with verification evidence.

See:

- [Product development workflow](docs/workflow.md)
- [Delivery registry](docs/workflow/README.md)
- [Delivery registry schema](docs/workflow/schema.md)

## Documentation

- [Architecture](docs/architecture.md)
- [Overall plan](docs/overall-plan.md)
- [Backend plan](docs/backend-plan.md)
- [Frontend plan](docs/frontend-plan.md)
- [Plugin package plan](docs/plugin-npm-package.md)
- [Task breakdown](docs/tasks.md)
