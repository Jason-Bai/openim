# OpenClaw IM 接入系统总方案（讨论版）

> 状态：方案讨论中，非最终版。
>
> 本文是项目总方案，负责说明业务背景、系统目标、整体架构、主流程、模块优先级、技术栈推荐和总体验收。前端、后端、Plugin 分别独立成文，本文只引用关键结论。

---

# 1. 背景

公司内部有 2000+ 员工，每个员工最终都需要拥有一个 OpenClaw 员工助手。

OpenClaw 在本项目里的定义是：

> **员工账号人格 / 身份对应的员工助手 BOT。**

OpenClaw 员工助手不是员工登录账号，也不是 Web 客户端。员工先在本项目中注册系统账号，然后通过默认 BOT 创建一个 BOT 接入槽位，再把 `/connect {bot_id}` 输出的连接信息复制给公司工单创建出来的 OpenClaw 员工助手。OpenClaw 员工助手拿到连接信息后，通过官方 npm Plugin 接入本项目。

第一阶段的关键不是先做完整 IM，而是先把这条链路跑通：

```text
员工账号
  ↓
默认 BOT
  ↓
/new-bot 创建 bot_id
  ↓
/connect {bot_id} 获取连接信息
  ↓
OpenClaw 员工助手通过 npm Plugin 接入
  ↓
服务端鉴权、握手、绑定
  ↓
Web 端可查看 OpenClaw 员工助手已连接
```

P0 只证明接入链路成立。员工与 OpenClaw 员工助手基础单聊进入 P1；后续员工自建 BOT、主区、子区、文件、压测都建立在这条接入链路之上。

---

# 2. 当前要解决的问题

## 2.1 业务问题

员工已经可以通过公司工单获得 OpenClaw 员工助手，但这个助手还没有标准方式接入本项目。

系统必须解决：

- 员工如何在本系统中生成一个可接入的 BOT 身份。
- OpenClaw 员工助手如何拿到连接信息。
- OpenClaw 员工助手如何接入服务端。
- 服务端如何确认这个助手属于哪个员工。
- 员工如何看到助手的连接状态。
- 员工如何和助手发送消息。

## 2.2 技术问题

系统必须补齐：

- 前端 Web 操作入口
- 后端用户、BOT、绑定、消息服务
- BOT Gateway
- npm Plugin
- WebSocket 协议
- 鉴权与 token 管理
- 心跳、断线重连、状态机
- 可观测日志和错误码

## 2.3 文档拆分问题

总方案不能把所有细节揉在一起。本文只保留总览和决策，细节拆到独立文档：

```text
docs/overall-plan.md          总方案
docs/frontend-plan.md         前端独立方案
docs/backend-plan.md          后端独立方案
docs/plugin-npm-package.md    Plugin 独立方案
docs/v1.md                    原始草稿归档
docs/v2.md                    上一版讨论稿归档
```

---

# 3. 推荐技术栈

这里直接给第一版推荐，不再保留多选。

## 3.1 前端推荐

详见 `docs/frontend-plan.md`。

推荐：

```text
语言：TypeScript
框架：React
构建：Vite
路由：React Router
服务端状态：TanStack Query
局部状态：Zustand
UI：Ant Design
通信：REST + WebSocket
```

推荐理由：

- React + Vite 适合快速搭建 Web IM 管理界面。
- TanStack Query 适合处理登录用户、BOT 列表、会话、历史消息等服务端状态。
- Zustand 适合保存当前会话、输入状态、WebSocket 连接状态等轻量客户端状态。
- Ant Design 适合内部系统，表单、列表、状态标签、弹窗、复制代码块等组件齐全，能降低第一版 UI 成本。

## 3.2 后端推荐

详见 `docs/backend-plan.md`。

推荐：

```text
语言：Python 3.12
框架：FastAPI
ASGI Server：Uvicorn
API Schema：Pydantic v2
WebSocket：FastAPI WebSocket
数据库：MySQL 8
缓存：Redis
ORM：SQLAlchemy 2.x
数据库迁移：Alembic
认证：JWT
配置：pydantic-settings
测试：pytest
对象存储：MinIO 预留，P3 再落地文件能力
```

推荐理由：

- FastAPI 适合 P0 快速打通 REST + WebSocket + Plugin Gateway 链路。
- Pydantic v2 可以把 REST 响应、BOT Gateway 协议和配置项固化为可验证模型。
- SQLAlchemy 2.x + Alembic 能覆盖 MySQL schema、迁移和事务需求。
- MySQL 负责用户、BOT、绑定、消息等强一致数据。
- Redis 负责在线状态、连接状态、限流、短期会话。
- P0 BOT Gateway 使用 FastAPI WebSocket。独立 Gateway 服务不进入 P0，只有在 P3 压测发现单体 FastAPI 无法满足连接规模或延迟目标时再立项。

## 3.3 Plugin 推荐

详见 `docs/plugin-npm-package.md`。

推荐：

```text
包名：@openim/openclaw-bot-plugin
状态：待开发
定位：本项目官方基础 SDK npm package
语言：TypeScript
运行环境：Node.js 18+
协议：WebSocket JSON
打包：tsup
模块格式：ESM + CommonJS
发布形态：npm package
```

推荐理由：

- OpenClaw 员工助手侧需要一个可安装、可升级、可版本化的标准接入 SDK。
- npm package 比单文件插件更适合版本管理、类型声明、依赖管理和后续升级。
- TypeScript 可以把协议、消息、错误码固化成类型，降低接入错误。

---

# 4. 系统目标与非目标

## 4.1 第一阶段目标

P0 只做能作为地基的 MVP：

- 员工注册 / 登录
- 默认 BOT 会话入口
- 默认 BOT 6 条命令
- 默认 BOT 命令 REST 通道：`POST /api/default-bot/commands`
- `/new-bot` 创建 BOT 接入槽位
- `/connect {bot_id}` 输出 npm Plugin 连接信息
- OpenClaw 员工助手通过 Plugin 接入 BOT Gateway
- `bot_id + token` 鉴权
- Plugin 自动 handshake
- 服务端建立绑定：`user_id -> bot_id -> OpenClaw 员工助手`
- Web 端展示 BOT 状态
- 接入过程可验证、可排查

## 4.2 第一阶段非目标

第一阶段不做：

- 员工与 OpenClaw 员工助手基础单聊
- 主区 / 子区
- 文件上传下载
- 公司工单系统自动同步
- 多语言 Plugin SDK
- 浏览器端 Plugin
- 复杂权限系统
- 完整后台管理台
- 2000 人压测自动化

这些进入 P1/P2/P3。

---

# 5. 核心定义

## 5.1 员工系统账号

员工在本系统注册的登录账号。

用途：

- 登录 Web 端
- 使用默认 BOT
- 创建 BOT 接入槽位
- 获取连接信息
- 查看 OpenClaw 员工助手状态
- 与 OpenClaw 员工助手聊天

## 5.2 默认 BOT

默认 BOT 是系统级内置管理入口。

默认 BOT 用于帮助员工完成 OpenClaw 员工助手和个人 BOT 接入，不等于 OpenClaw 员工助手，也不等于任何外部接入 BOT。

每个员工账号创建后，默认具备一个系统级默认 BOT 会话入口。默认 BOT 是系统能力，不需要员工接入，不需要 Plugin，也不进入普通 `bots` 表。

默认 BOT 的第一版命令：

```text
/help
/my-bots
/new-bot
/delete-bot {bot_id}
/connect {bot_id}
/disconnect {bot_id}
```

说明：

- `/connect {bot_id}` 输出指定 BOT 的连接信息，不直接建立连接。
- 如果 token 已经展示过，`/connect {bot_id}` 返回 masked token，并在员工二次确认后重新生成 token。
- `/disconnect {bot_id}` 临时断开指定 BOT 的当前连接，不撤销绑定，不删除 token。
- 无参 `/connect`、`/disconnect` 只作为交互辅助：默认 BOT 返回当前员工名下 BOT 列表，并提示员工选择 `bot_id`，不自动猜测。

## 5.3 BOT 接入槽位

员工通过 `/new-bot` 创建的系统内 BOT 身份。

普通 `bots` 表只保存需要外部接入的 BOT：

- `openclaw_assistant`：公司工单创建的 OpenClaw 员工助手
- `custom_bot`：员工后续个人自建 BOT

`system_default_bot` 是系统内置身份，不放入普通 `bots` 表。

接入槽位保存：

- `bot_id`
- token hash
- 归属员工账号
- BOT 类型
- 连接状态
- 首次连接时间
- 最近心跳时间

绑定状态不放在 BOT 表中，统一由 `user_bot_bindings.status` 维护，避免双写不一致。

## 5.4 OpenClaw 员工助手

员工通过公司工单获得的助手 BOT。

它拿到 `/connect {bot_id}` 输出的连接信息后，通过 `@openim/openclaw-bot-plugin` 连接 BOT Gateway。

## 5.5 Plugin

Plugin 是本项目待开发的官方基础 SDK npm package，不是已有第三方包。

包名固定：

```text
@openim/openclaw-bot-plugin
```

职责：

- WebSocket 建连
- 鉴权
- handshake
- 心跳
- 断线重连
- 错误处理

P1 基础单聊阶段补充：

- 接收消息
- 发送消息

---

# 6. 总体架构

```text
┌────────────────────┐
│     员工 Web 端     │
│ React + Vite       │
└─────────┬──────────┘
          │ REST / WebSocket
          ▼
┌────────────────────────────────────┐
│        OpenClaw IM 服务端           │
│ FastAPI + Uvicorn                   │
│                                    │
│  ├─ 用户与认证                      │
│  ├─ 默认 BOT 命令系统               │
│  ├─ BOT 管理                        │
│  ├─ BOT Gateway                     │
│  ├─ 绑定服务                        │
│  ├─ 会话与消息                      │
│  └─ 连接日志                        │
└───────┬──────────────┬─────────────┘
        │              │
        ▼              ▼
   MySQL 8          Redis

┌────────────────────────┐
│  OpenClaw 员工助手      │
│  Node.js Runtime       │
└───────────┬────────────┘
            │ @openim/openclaw-bot-plugin
            ▼
       BOT Gateway
```

边界：

- 员工 WebSocket 和 BOT Gateway WebSocket 分开。
- 默认 BOT 是服务端内置命令系统。
- OpenClaw 员工助手是外部 Runtime。
- Plugin 是 OpenClaw 员工助手侧的 SDK。

---

# 7. P0 主流程

## 7.1 项目初始化

项目初始化不属于单个员工的接入流程，但必须先存在：

- 用户注册 / 登录
- 默认 BOT 服务
- 默认 BOT 会话入口
- 默认 BOT 命令框架
- BOT 管理表
- BOT Gateway
- npm Plugin 方案

## 7.2 员工接入 OpenClaw 员工助手

```text
员工注册并登录系统账号
  ↓
进入默认 BOT 会话
  ↓
输入 /new-bot
  ↓
后端创建 BOT 接入槽位，生成 bot_id
  ↓
员工输入 /connect {bot_id}
  ↓
默认 BOT 返回连接信息
  ↓
员工复制连接信息给 OpenClaw 员工助手
  ↓
OpenClaw 员工助手安装/使用 @openim/openclaw-bot-plugin
  ↓
Plugin 连接 BOT Gateway
  ↓
BOT Gateway 校验 bot_id + token
  ↓
Plugin 自动发送 handshake
  ↓
服务端建立绑定：员工账号 -> bot_id -> OpenClaw 员工助手
  ↓
Web 端显示 OpenClaw 员工助手已连接
```

## 7.3 `/connect {bot_id}` 输出示例

```json
{
  "bot_id": "bot_01HX7K9A2M4Q8R6T3ZP",
  "token": "ocb_live_xxx",
  "gateway_url": "wss://im.company.com/bot-gateway/ws",
  "protocol_version": "bot-v1",
  "plugin": {
    "type": "npm",
    "package": "@openim/openclaw-bot-plugin",
    "version": "0.1.0",
    "install": "npm install ./openim-openclaw-bot-plugin-0.1.0.tgz",
    "docs": "docs/plugin-npm-package.md"
  }
}
```

## 7.4 token 生命周期

第一版 token 策略：

```text
默认不过期，仅支持主动重新生成 / revoke。
```

原因：

- P0 的核心是打通员工复制连接信息给 OpenClaw 员工助手的接入链路。
- 短期 token 会增加工单、复制、调试成本。
- 安全风险通过 revoke、重新生成 token、token hash、日志脱敏控制。

说明：

- `TOKEN_EXPIRED` 错误码作为协议预留，P0 不启用自动过期。
- token 明文只在 `/connect {bot_id}` 输出时展示。
- 数据库只存 token hash。

`/connect {bot_id}` 命令语义：

- 默认执行幂等读取连接信息。
- 重复调用不会自动重新生成 token。
- 重复调用不会让旧 token 失效。
- 如果当前 token 明文仍未展示过，返回完整 token，并记录 `token_revealed_at`。
- 如果当前 token 明文已经展示过，返回 masked token，并提示员工是否重新生成 token。
- 员工二次确认后，默认 BOT 调用后端接口生成新 token。

token 重新生成语义：

- 员工不需要记忆单独的 token 命令，命令层复用 `/connect {bot_id}` 完成二次确认。
- 后端提供 `POST /api/bots/{bot_id}/connect-info/regenerate` 给默认 BOT handler 调用。
- 新 token 明文只展示一次。
- P0 固定为旧 token 立即失效。
- 正在使用旧 token 的 Plugin 需要重新配置并重连。

## 7.5 连接状态与绑定状态

连接状态分两层：

```text
MySQL bots.connect_status      最后一次持久化连接状态
Redis bot:online:{bot_id}      当前实时在线状态
```

实时在线状态以 Redis 为准，MySQL 用于历史、展示兜底和审计。

更新规则：

- 鉴权开始：`bots.connect_status = authenticating`
- handshake 成功：`bots.connect_status = connected`，Redis 写入在线状态
- 心跳正常：Redis 刷新 TTL，MySQL 节流更新 `last_seen_at`
- 主动 `/disconnect {bot_id}`：删除 Redis 在线状态，`bots.connect_status = disconnected`
- 心跳超时：Redis key 过期，后台任务或网关事件把 MySQL 修正为 `disconnected`
- 服务重启：执行 startup cleanup，把 `connected/authenticating` 修正为 `disconnected`

绑定状态只由 `user_bot_bindings.status` 维护。

```text
disconnect = 临时断开，可重连，绑定仍 active，token 仍可用
delete-bot = 删除未使用或已断开的 BOT 槽位
revoke = 撤销身份绑定和 token，不能再接入
```

---

# 8. 模块优先级

## P0-A：系统级初始化与员工账号

目标：员工可以进入系统并使用默认 BOT。

范围：

- 员工注册
- 员工登录
- JWT
- 系统内置 `system_default_bot`
- 默认 BOT 会话初始化机制
- 默认 BOT 会话入口
- 默认 BOT 命令框架
- `/help`

验收：

- 员工可注册。
- 员工可登录。
- 登录后会话列表出现默认 BOT。
- `/help` 返回稳定帮助信息。
- 默认 BOT 不进入普通 `bots` 表。

## P0-B：OpenClaw 员工助手接入

目标：员工通过默认 BOT 创建接入槽位，并把 OpenClaw 员工助手接入系统。

范围：

- `/new-bot`
- `/connect {bot_id}`
- `bot_id` 生成
- token 生成与 hash 存储
- `/connect {bot_id}` 幂等读取连接信息
- `/connect {bot_id}` 二次确认后重新生成 token
- BOT Gateway
- Plugin 接入
- 鉴权
- handshake
- 绑定关系

验收：

- `/new-bot` 创建 `pending` 状态 BOT。
- `/connect {bot_id}` 返回完整连接信息。
- 重复 `/connect {bot_id}` 不自动重新生成 token。
- token 已展示后再次 `/connect {bot_id}` 返回 masked token。
- 员工二次确认后可通过 `/connect {bot_id}` 重新生成 token。
- Plugin 使用正确凭证可连接。
- 错误 token 被拒绝。
- handshake 成功后建立绑定。
- Web 端显示已连接。

## P0-C：可验证与可排查

目标：接入失败时能定位原因。

范围：

- MySQL `pending/authenticating/connected/disconnected/revoked`
- Redis 实时在线状态
- `first_connected_at`
- `last_seen_at`
- `request_id`
- `trace_id`
- 连接日志
- 错误码
- 心跳超时
- 断线重连

验收：

- 鉴权失败有明确错误码。
- 心跳超时后状态变为 `disconnected`。
- 断线重连后状态恢复。
- 每次连接可追踪。

## P1：基础 IM

目标：员工与 OpenClaw 员工助手可以单聊。

范围：

- 会话列表
- 单聊消息
- 员工 WebSocket
- 消息落库
- 历史消息

验收：

- 员工能给 OpenClaw 员工助手发消息。
- OpenClaw 员工助手能回复员工。
- 历史消息可查询。

## P2：员工自建 BOT

目标：后续员工自己的 BOT 复用已走通的接入链路。

范围：

- 多 BOT 管理
- `bot_type`
- 自定义 BOT 名称
- 自建 BOT 权限范围

验收：

- 同一员工可以创建多个 BOT。
- 可以区分 `openclaw_assistant` 和 `custom_bot`。
- 自建 BOT 复用 `/new-bot`、`/connect {bot_id}`、Plugin、BOT Gateway。

## P3：扩展 IM 与运维

目标：完善公司 IM 能力和上线运行能力。

范围：

- 主区
- 子区
- 文件
- Redis 在线状态
- 监控
- 告警
- 部署
- 2000 人压测

验收：

- 主区 / 子区消息正常。
- 文件上传下载正常。
- 2000 人在线压测稳定。
- 关键指标可监控。

---

# 9. 子方案引用

## 9.1 前端方案

文档：

```text
docs/frontend-plan.md
```

负责：

- 页面结构
- 前端状态
- 默认 BOT 会话交互
- `/connect {bot_id}` 复制体验
- WebSocket 消息展示
- 前端验收

## 9.2 后端方案

文档：

```text
docs/backend-plan.md
```

负责：

- 服务模块
- REST API
- WebSocket
- BOT Gateway
- 数据模型
- 安全
- 后端验收

## 9.3 Plugin 方案

文档：

```text
docs/plugin-npm-package.md
```

负责：

- npm package 定义
- SDK API
- WebSocket JSON 协议
- 鉴权与 handshake
- 心跳与重连
- 错误码
- Plugin 验收

---

# 10. 总体验收标准

## P0 验收

- [ ] 员工可注册并登录。
- [ ] 员工登录后能看到默认 BOT。
- [ ] `/help` 可用。
- [ ] `/new-bot` 可创建 BOT 接入槽位。
- [ ] `/connect {bot_id}` 可返回 npm Plugin 接入信息。
- [ ] OpenClaw 员工助手使用 Plugin 可连接 BOT Gateway。
- [ ] token 错误时连接失败。
- [ ] handshake 成功后建立员工账号与 BOT 绑定。
- [ ] Web 端可查看 BOT 已连接。
- [ ] 接入失败可通过错误码和日志定位。

## P1/P2/P3 验收

各阶段验收以独立方案为准：

- 前端验收见 `docs/frontend-plan.md`
- 后端验收见 `docs/backend-plan.md`
- Plugin 验收见 `docs/plugin-npm-package.md`

---

# 11. 风险与处理

## 11.1 OpenClaw 员工助手运行环境不确定

风险：如果 OpenClaw 员工助手不能运行 Node.js，则 npm Plugin 无法直接接入。

处理：第一版先确认并固定 Node.js 18+。如果不满足，再设计 HTTP Bridge 或其他语言 SDK。

## 11.2 token 泄露

风险：员工复制连接信息时可能泄露 token。

处理：

- token 明文只展示一次；员工丢失 token 时，通过 `/connect {bot_id}` 的二次确认流程重新生成 token。
- 数据库只存 hash。
- 日志禁止打印完整 token。
- 支持撤销 BOT。

## 11.3 BOT Gateway 与普通 WebSocket 混用

风险：协议、鉴权、限流、状态管理互相污染。

处理：BOT Gateway 独立路径 `/bot-gateway/ws`，员工 WebSocket 使用 `/ws`。

## 11.4 一开始就做完整 IM

风险：主区、子区、文件、压测会拖慢 OpenClaw 接入主链路。

处理：P0 只保证接入、绑定、状态闭环；员工与 OpenClaw 员工助手的消息闭环进入 P1。

---

# 12. P0 前置假设

1. OpenClaw 员工助手运行环境支持 Node.js 18+，可以安装并运行 `@openim/openclaw-bot-plugin`。
2. 公司工单系统第一版不做自动同步，员工通过默认 BOT 复制连接信息，并人工交给 OpenClaw 员工助手。
3. P0 联调阶段 Plugin 不发布到公开 npm，使用 `npm pack` 生成 tarball 后安装。
4. 后端通过 `BOT_GATEWAY_PUBLIC_URL` 配置 `/connect {bot_id}` 输出的 `gateway_url`，不从 HTTP request host 推导。
5. JWT 使用 HS256，默认有效期 7 天，P0 不做 refresh token。

如果第 1 条不成立，需要先补充 HTTP Bridge 或其他语言 SDK 方案；如果第 2 条不成立，工单系统集成需要单独进入 P1/P2 范围。

---

# 13. P0 开发默认约定

## 13.1 Plugin 安装

P0 联调安装方式固定为本地 tarball：

```bash
cd packages/openclaw-bot-plugin
npm pack
npm install ./openim-openclaw-bot-plugin-0.1.0.tgz
```

公开 npm 发布、私有 npm registry、自动发布流程不进入 P0。

## 13.2 运行时配置

后端 P0 必填配置：

```text
BOT_GATEWAY_PUBLIC_URL=wss://im.company.com/bot-gateway/ws
JWT_SECRET=<env secret>
JWT_EXPIRES_IN=7d
```

前端 P0 配置：

```text
VITE_API_BASE_URL=/api
VITE_WS_BASE_URL=ws://localhost:8080
```

开发环境使用 Vite proxy 把 `/api` 转发到 `http://localhost:8080`。

## 13.3 ID 与 token

```text
bot_id: bot_ + ULID
token: ocb_live_ + 32 bytes secure random Base58
masked token: ocb_live_****_{last4}
request_id: 客户端传入则原样回传，未传则服务端生成 UUID v4
conversation_id: 数据库普通主键，业务语义由 conversation_type + target_type + target_id 表达
```

## 13.4 安全与超时

```text
password hash: bcrypt rounds 12
JWT: HS256, 7d, secret from env
Plugin heartbeat interval: 30s
Redis bot online TTL: 100s
离线判定阈值: 90s
BOT Gateway auth timeout: 15s
AUTH_TIMEOUT close code: 4000
AUTH_TIMEOUT close reason: AUTH_TIMEOUT
```
