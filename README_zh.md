# OpenIM

OpenIM 是一个轻量级内部 IM 原型，用于连接员工账号和 OpenClaw 员工助手 BOT。

它包含 Web 聊天界面、FastAPI 后端、BOT Gateway WebSocket 协议，以及给外部/OpenClaw BOT Runtime 使用的官方 Node.js 插件包。

English documentation: [README.md](README.md)

## 为什么是 OpenIM

OpenIM 探索一种简单的员工助手接入模型：

```text
员工账号 -> 默认 BOT -> BOT 槽位 -> OpenClaw plugin -> BOT Gateway -> 会话
```

目标是让 BOT onboarding、连接状态、联系人、会话和消息历史都由后端支撑，并且能在本地稳定复现和验证。

## 功能

- 员工注册与登录。
- 默认 BOT，用于 onboarding 和 BOT 管理。
- 通过 `/new-bot` 创建 BOT 槽位。
- 通过 `/connect {bot_id}` 生成连接信息。
- BOT Gateway WebSocket 鉴权、握手、心跳和重连支持。
- 后端持久化 conversations 和 message history。
- 默认 BOT、OpenClaw BOT、员工联系人和聊天 UI。
- 官方 BOT SDK 包：`@openim/openclaw-bot-plugin`。

## 技术栈

| 模块 | 技术 |
|---|---|
| Web | React, Vite, TypeScript, TanStack Query, Zustand, Ant Design |
| Server | Python, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2.x, Alembic |
| 本地数据 | SQLite |
| 规划服务 | MySQL, Redis |
| BOT SDK | TypeScript, Node.js 18+, WebSocket JSON, tsup |

## 项目结构

```text
openim/
  apps/
    web/                         # React Web 客户端
    server/                      # FastAPI 后端
  packages/
    openclaw-bot-plugin/         # 官方 BOT SDK 包
  scripts/                       # 本地 smoke 和 bridge 脚本
  docs/                          # 架构、产品、流程和测试文档
```

## 快速开始

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

另开一个终端启动前端：

```bash
npm run dev -w apps/web
```

打开应用：

```text
http://127.0.0.1:5173
```

## 常用命令

后端：

```bash
cd apps/server && uv run pytest -q
cd apps/server && uv run ruff check .
```

前端：

```bash
npm run test -w apps/web
npm run build -w apps/web
```

Smoke 测试：

```bash
npm run e2e:p0
npm run e2e:p0:plugin
npm run e2e:p05
npm run e2e:openclaw:local
```

`e2e:p05` 需要后端运行在 `127.0.0.1:8080`。

本地 OpenClaw bridge smoke 默认使用：

```text
OPENCLAW_CONTROL_URL=http://127.0.0.1:18789
```

## 开发流程

非 trivial 工作使用：

- GitHub Issues 作为工作入口。
- 每个需求独立的 delivery registry 文件。
- 隔离分支和 worktree。
- 带验证证据的 Pull Request。

参考：

- [产品研发流程](docs/workflow.md)
- [Delivery registry](docs/workflow/README.md)
- [Delivery registry schema](docs/workflow/schema.md)

## 文档

- [架构](docs/architecture.md)
- [总方案](docs/overall-plan.md)
- [后端方案](docs/backend-plan.md)
- [前端方案](docs/frontend-plan.md)
- [Plugin package 方案](docs/plugin-npm-package.md)
- [任务拆解](docs/tasks.md)
