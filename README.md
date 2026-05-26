# OpenIM

OpenIM 是一个用于接入 OpenClaw 员工助手的内部 IM 与 BOT Gateway 项目。

当前 P0 已落地为可本地运行的最小闭环：员工注册登录后从通讯录或首屏引导打开默认 BOT，会话按需创建；随后通过 `/new-bot` 创建 OpenClaw 员工助手接入槽位，通过 `/connect {bot_id}` 获取连接信息，外部助手或本地验证脚本使用 BOT Gateway 完成 auth、handshake、heartbeat 后建立员工账号到 OpenClaw 员工助手的绑定。

## Project Naming

GitHub repository 推荐名称：

```text
openim
```

如果 GitHub 上 `openim` 不可用或容易混淆，备选：

```text
openclaw-openim
```

## Recommended Structure

```text
openim/
  apps/
    web/                         # openim-web
    server/                      # openim-server
  packages/
    openclaw-bot-plugin/         # @openim/openclaw-bot-plugin
  docs/
```

## Components

### Frontend

```text
path: apps/web
app: openim-web
package: @openim/web
stack: React + Vite + TypeScript + TanStack Query + Zustand + Ant Design
```

### Backend

```text
path: apps/server
service: openim-server
stack: Python 3.12 + FastAPI + Uvicorn + Pydantic v2 + SQLAlchemy 2.x + Alembic + MySQL 8 + Redis + JWT
python package: openim_server
```

### Plugin

```text
path: packages/openclaw-bot-plugin
package: @openim/openclaw-bot-plugin
status: P0 基础包已实现
positioning: 本项目官方基础 SDK npm package
stack: TypeScript + Node.js 18+ + WebSocket JSON + tsup
```

## Local P0 Runbook

安装依赖：

```bash
npm install
cd apps/server && uv sync --dev
```

启动后端：

```bash
cd apps/server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080
```

启动前端：

```bash
npm run dev -w apps/web
```

打开前端：

```text
http://127.0.0.1:5173
```

一键验证 P0 主链路：

```bash
npm run e2e:p0
```

使用真实 Plugin SDK 构建产物验证外部助手接入链路：

```bash
npm run e2e:p0:plugin
```

使用本机 OpenClaw 地址验证 OpenClaw 可达性 + OpenIM 接入闭环：

```bash
npm run e2e:openclaw:local
```

默认 OpenClaw 地址：

```text
OPENCLAW_CONTROL_URL=http://127.0.0.1:18789
```

如果需要额外让 OpenClaw agent 回复一次 smoke 消息：

```bash
OPENCLAW_AGENT_SMOKE=1 npm run e2e:openclaw:local
```

验证范围：

```text
注册员工账号 -> 打开默认 BOT -> /new-bot -> /connect {bot_id}
-> BOT Gateway auth -> handshake -> heartbeat
-> binding_status=active 且 connect_status=connected
```

`e2e:p0:plugin` 会额外通过 `@openim/openclaw-bot-plugin` 的构建产物完成连接，验证外部 BOT 按 npm package SDK 接入时也能完成绑定。

`e2e:openclaw:local` 会先确认本机 OpenClaw Control 和 Gateway 可达，再执行同一条 OpenIM 默认 BOT 接入链路。

## P0.5 Manual Acceptance

- [ ] 通讯录“已添加的 AI” shows 默认 BOT and OpenClaw 员工助手.
- [ ] 通讯录“全部联系人” shows 默认 BOT, OpenClaw 员工助手, and current employee.
- [ ] Clicking a contact opens profile, not a conversation.
- [ ] Clicking 发送消息 creates/opens the conversation.
- [ ] Default BOT appears in 会话 only after opening/sending.
- [ ] OpenClaw BOT status changes online/offline without refresh.
- [ ] OpenClaw BOT remains usable after backend restart and Plugin reconnect.

## Documents

- [总方案](docs/overall-plan.md)
- [前端方案](docs/frontend-plan.md)
- [后端方案](docs/backend-plan.md)
- [Plugin npm package 方案](docs/plugin-npm-package.md)
- [v1 原始草稿](docs/v1.md)
- [v2 讨论稿](docs/v2.md)
