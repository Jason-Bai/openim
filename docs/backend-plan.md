# OpenClaw IM 后端方案（讨论版）

> 状态：方案讨论中，非最终版。
>
> 本文只描述后端。总方案见 `docs/overall-plan.md`，前端见 `docs/frontend-plan.md`，Plugin 见 `docs/plugin-npm-package.md`。

---

# 1. 后端目标

P0 后端目标：

- 支持员工注册 / 登录。
- 初始化默认 BOT 会话入口。
- 处理默认 BOT 命令。
- 提供默认 BOT 命令 REST 通道：`POST /api/default-bot/commands`。
- 支持 `/new-bot` 创建 BOT 接入槽位。
- 支持 `/connect {bot_id}` 输出 Plugin 连接信息。
- 提供 BOT Gateway WebSocket。
- 校验 `bot_id + token`。
- 接收 Plugin handshake 并建立绑定。
- 提供可排查日志、状态和错误码。

P1 后端目标：

- 支持员工与 OpenClaw 员工助手基础单聊。
- 提供员工 WebSocket `/ws`。
- 提供消息落库、历史消息和会话 last_message 能力。

---

# 2. 推荐技术栈

第一版直接推荐：

```text
language: Python 3.12
framework: FastAPI
server: Uvicorn
api schema: Pydantic v2
websocket: FastAPI WebSocket
database: MySQL 8
cache: Redis
migration: Alembic
orm: SQLAlchemy 2.x
auth: JWT
config: pydantic-settings
test: pytest
object storage: MinIO 预留，P3 再落地文件能力
```

推荐理由：

- FastAPI 适合 P0 快速打通 REST + WebSocket + Plugin Gateway 链路。
- Pydantic v2 用于统一 REST 响应、BOT Gateway 协议模型和配置校验。
- SQLAlchemy 2.x + Alembic 负责 MySQL 访问、事务和 schema 迁移。
- MySQL 负责用户、BOT、绑定、消息等强一致数据。
- Redis 负责在线状态、连接状态、限流、短期会话。
- P0 BOT Gateway 使用 FastAPI WebSocket。独立 Gateway 服务不进入 P0，只有在 P3 压测发现单体 FastAPI 无法满足连接规模或延迟目标时再立项。

---

# 3. P0 运行配置

P0 后端必填环境变量：

```text
BOT_GATEWAY_PUBLIC_URL=wss://im.company.com/bot-gateway/ws
JWT_SECRET=<env secret>
JWT_EXPIRES_IN=7d
```

说明：

- `/connect {bot_id}` 返回的 `gateway_url` 固定读取 `BOT_GATEWAY_PUBLIC_URL`。
- 服务端不从 HTTP request host 推导 `gateway_url`，避免代理、内网域名、HTTP/HTTPS 转换导致接入信息错误。
- JWT 使用 HS256，secret 只从环境变量读取。
- P0 JWT 有效期固定为 7 天，不做 refresh token。
- JWT 过期后 REST 返回 `UNAUTHORIZED`，前端清理登录态并回到登录页。

本地开发环境：

```text
backend: http://localhost:8080
mysql: localhost:3306
redis: localhost:6379
```

P0 提供 `docker-compose.yml` 启动 MySQL 8 和 Redis。

Python 依赖管理：

```text
dependency manager: uv
runtime: Python 3.12
entrypoint: uvicorn app.main:app --host 0.0.0.0 --port 8080
```

---

# 4. 后端模块

```text
auth-service
user-service
conversation-service
default-bot-service
bot-management-service
bot-gateway
binding-service
connection-log-service
message-service（P1）
```

## 4.1 auth-service

职责：

- 注册
- 登录
- 密码哈希
- token 签发
- 当前用户解析

默认约定：

- 密码使用 bcrypt hash。
- bcrypt rounds 固定为 12。
- JWT 使用 HS256。
- JWT 有效期固定为 7 天。

## 4.2 default-bot-service

职责：

- 维护系统内置 `system_default_bot` 身份
- 初始化默认 BOT 会话入口
- 在员工账号创建后确保默认 BOT 会话存在
- 在员工登录时执行幂等补偿 `ensureDefaultBotConversation(user_id)`
- 解析默认 BOT 命令
- 路由命令到对应 handler
- 生成 BOT 回复消息
- 提供 `POST /api/default-bot/commands`，P0 通过请求 / 响应执行命令，不依赖完整消息系统
- 管理默认 BOT 对话级 pending action，例如 token 重新生成确认

默认 BOT 是系统级服务，不是外部接入 BOT。它不进入普通 `bots` 表，不需要 Plugin，也不是 OpenClaw 员工助手接入流程中的一步。

命令：

```text
/help
/my-bots
/new-bot
/delete-bot {bot_id}
/connect {bot_id}
/disconnect {bot_id}
```

无参 `/connect` 和 `/disconnect` 只返回可选择的 BOT 列表，不自动选择目标 BOT。

token 重新生成确认规则：

- `/connect {bot_id}` 如果发现 token 已展示过，默认 BOT 进入 `pending_action = regenerate_token`。
- pending action 存 Redis，key 为 `bot:pending_action:{user_id}:{bot_id}`，TTL 5 分钟。
- pending action value 保存 `action`、`user_id`、`bot_id`、`confirm_text`、`created_at`、`expires_at`。
- 默认 BOT 提示员工输入 `confirm regenerate {bot_id}` 或 `cancel`。
- 输入正确 confirm：调用 `POST /api/bots/{bot_id}/connect-info/regenerate` 并返回新连接信息。
- 输入 `cancel`：取消 pending action。
- 输入其他内容：重新提示正确确认文本，不静默失败。
- 超过 5 分钟：pending action 过期，员工需要重新执行 `/connect {bot_id}`。

Redis value 示例：

```json
{
  "action": "regenerate_token",
  "user_id": "user_123",
  "bot_id": "bot_123",
  "confirm_text": "confirm regenerate bot_123",
  "created_at": "2026-05-25T10:00:00Z",
  "expires_at": "2026-05-25T10:05:00Z"
}
```

## 4.3 bot-management-service

职责：

- 创建 BOT 接入槽位
- 生成 `bot_id`
- 生成 token
- 存储 token hash
- 查询当前员工名下 BOT
- 撤销 BOT
- 输出 `/connect {bot_id}` 连接信息
- 保证 `/connect {bot_id}` 是幂等读取，不自动重新生成 token
- 支持默认 BOT handler 在员工二次确认后主动重新生成 token
- 处理 `/disconnect {bot_id}`

ID 与 token 生成规则：

```text
bot_id: bot_ + ULID
token: ocb_live_ + 32 bytes secure random Base58
masked token: ocb_live_****_{last4}
```

说明：

- `bot_id` 示例：`bot_01HX7K9A2M4Q8R6T3ZP`。
- ULID 由服务端生成，不依赖数据库自增序列。
- token 使用 Python `secrets.token_bytes(32)` 生成随机值，再编码为 Base58 字符串。
- 数据库只保存 token bcrypt hash。
- `last4` 取完整 token 最后 4 个字符；无法取值时返回 `[MASKED]`。

## 4.4 bot-gateway

职责：

- 提供 Plugin 专用 WebSocket 入口
- 接收 `auth`
- 校验 `bot_id + token`
- 接收 `handshake`
- 维护连接状态
- 接收心跳
- P1 接收 BOT outbound message
- P1 向 BOT 下发 inbound message

BOT Gateway 不和员工 WebSocket 混用。

网关超时：

- WebSocket 建连后 15 秒内必须收到 `auth` 消息。
- 超时未收到 `auth` 时关闭连接。
- close code：`4000`。
- close reason：`AUTH_TIMEOUT`。

## 4.5 binding-service

职责：

- 在 handshake 成功后建立绑定：

```text
user_id -> bot_id -> OpenClaw 员工助手
```

- 处理解绑
- 保留绑定审计记录

## 4.6 message-service

职责：

- 保存消息
- 查询历史消息
- 投递员工消息到 BOT Gateway
- 投递 BOT 回复到员工 WebSocket

说明：`message-service` 属于 P1。P0 默认 BOT 命令不走消息落库链路，只通过 `POST /api/default-bot/commands` 返回命令结果。

---

# 5. 通用后端约定

## 5.1 REST Response

所有 REST API 返回统一结构。

成功：

```json
{
  "request_id": "req_001",
  "ok": true,
  "data": {}
}
```

失败：

```json
{
  "request_id": "req_001",
  "ok": false,
  "error": {
    "code": "AUTH_FAILED",
    "message": "用户名或密码错误",
    "retryable": false
  }
}
```

规则：

- `request_id` 必须全链路透传。
- `ok = true` 时返回 `data`。
- `ok = false` 时返回 `error.code`、`error.message`、`error.retryable`。
- REST 错误码、员工 WebSocket 错误码、BOT Gateway 错误码使用同一套 code 命名。
- Plugin 协议使用同一套错误码子集。
- 客户端传入 `request_id` 时，服务端原样回传。
- 客户端未传 `request_id` 时，服务端生成 UUID v4。

## 5.2 HTTP 状态码映射

```text
400 VALIDATION_FAILED
401 UNAUTHORIZED / AUTH_FAILED
403 FORBIDDEN / BOT_NOT_OWNED
404 NOT_FOUND / BOT_NOT_FOUND
409 BOT_ALREADY_CONNECTED
429 RATE_LIMITED
500 INTERNAL_ERROR
```

说明：

- HTTP 状态码表达请求处理类别。
- 响应体仍固定使用 `{ request_id, ok, data/error }`。
- 前端业务判断以 `error.code` 为准。

## 5.3 统一错误码

P0 错误码：

```text
AUTH_FAILED                  用户名密码错误，或 bot_id/token 错误
AUTH_TIMEOUT                 BOT Gateway 建连后未在 15 秒内发送 auth
UNAUTHORIZED                 未登录、JWT 缺失或 JWT 无效
FORBIDDEN                    已登录但无权限
VALIDATION_FAILED            请求参数不合法
NOT_FOUND                    资源不存在
BOT_NOT_FOUND                BOT 不存在
BOT_NOT_OWNED                BOT 不属于当前员工
BOT_REVOKED                  BOT 已撤销
BOT_ALREADY_CONNECTED        同一个 bot_id 已存在活跃连接
TOKEN_INVALID                token 不合法
TOKEN_REGENERATED            token 已重新生成，旧连接失效
HANDSHAKE_FAILED             握手失败（BOT Gateway）
PROTOCOL_VERSION_UNSUPPORTED 协议版本不支持（BOT Gateway）
HEARTBEAT_TIMEOUT            心跳超时（BOT Gateway）
MESSAGE_FORMAT_INVALID       消息格式错误（BOT Gateway）
MESSAGE_SEND_FAILED          消息发送失败
CONVERSATION_LOAD_FAILED     会话加载失败
BOT_STATUS_SYNC_FAILED       BOT 状态同步失败
RATE_LIMITED                 请求或消息发送频率超限
INTERNAL_ERROR               服务端内部错误
```

前端处理规则：

- `UNAUTHORIZED`：清理登录态并回到登录页。
- `retryable = true`：允许用户重试。
- `retryable = false`：只展示错误，不自动重试。

---

# 6. 核心接口

## 6.1 Auth REST

```text
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
```

## 6.2 User REST

```text
GET /api/users
```

说明：

- 返回系统内所有员工账号列表，用于前端通讯录「全部联系人」展示。
- P0 不做分页，员工规模在 2000 以内，一次返回完整列表。
- 不返回 password_hash 等敏感字段，只返回 id/username/employee_id/real_name。
- 需要 JWT 鉴权，未登录返回 `UNAUTHORIZED`。

## 6.3 Bot REST

```text
GET    /api/bots
POST   /api/bots
GET    /api/bots/{bot_id}
GET    /api/bots/{bot_id}/connect-info
POST   /api/bots/{bot_id}/connect-info/regenerate
POST   /api/bots/{bot_id}/disconnect
DELETE /api/bots/{bot_id}
```

这些接口主要供默认 BOT 命令 handler 和前端状态展示复用。

## 6.4 Default Bot REST

```text
POST /api/default-bot/commands
```

请求：

```json
{
  "conversation_id": "conv_default_bot",
  "command": "/connect bot_123"
}
```

响应：

```json
{
  "request_id": "req_001",
  "ok": true,
  "data": {
    "reply_type": "text",
    "content": "..."
  }
}
```

说明：

- P0 默认 BOT 命令通过该接口执行。
- 该接口必须校验 JWT，只能操作当前员工自己的 BOT。
- P0 不要求命令消息落库。
- P1 引入 `messages` 后，默认 BOT 命令可复用消息链路，但接口语义保持兼容。

## 6.5 Conversation REST

```text
GET /api/conversations
```

说明：

- P0 返回会话壳：默认 BOT 会话、当前员工已接入 BOT 会话。
- P0 不返回历史消息，不要求 `last_message`。
- P1 增加 `last_message_id`、`last_message_at`、未读数等消息相关字段。

## 6.6 Message REST（P1）

```text
GET  /api/conversations/{conversation_id}/messages
POST /api/messages
```

## 6.7 WebSocket

员工 WebSocket（P1）：

```text
/ws
```

BOT Gateway：

```text
/bot-gateway/ws
```

员工 WebSocket 和 BOT Gateway WebSocket 是两套协议，不混用。

## 6.8 员工 WebSocket 协议（P1）

员工 WebSocket 用于 Web 端接收新消息、消息状态和 BOT 状态变化。

所有服务端下发消息都包含：

```text
type
request_id
created_at
```

### message.new

```json
{
  "type": "message.new",
  "request_id": "req_002",
  "conversation_id": "conv_001",
  "message": {
    "message_id": "msg_001",
    "sender_type": "bot",
    "sender_id": "bot_01HX7K9A2M4Q8R6T3ZP",
    "content_type": "text",
    "content": "收到",
    "created_at": "2026-05-24T10:00:01Z"
  },
  "created_at": "2026-05-24T10:00:01Z"
}
```

### message.status

```json
{
  "type": "message.status",
  "request_id": "req_003",
  "message_id": "msg_001",
  "status": "sent",
  "created_at": "2026-05-24T10:00:02Z"
}
```

### bot.status_changed

```json
{
  "type": "bot.status_changed",
  "request_id": "req_004",
  "bot_id": "bot_01HX7K9A2M4Q8R6T3ZP",
  "connect_status": "connected",
  "last_seen_at": "2026-05-24T10:00:00Z",
  "created_at": "2026-05-24T10:00:00Z"
}
```

### conversation.updated

```json
{
  "type": "conversation.updated",
  "request_id": "req_005",
  "conversation_id": "conv_001",
  "last_message_id": "msg_001",
  "updated_at": "2026-05-24T10:00:02Z",
  "created_at": "2026-05-24T10:00:02Z"
}
```

### error

```json
{
  "type": "error",
  "request_id": "req_006",
  "code": "MESSAGE_SEND_FAILED",
  "message": "消息发送失败，请重试",
  "retryable": true,
  "related_id": "msg_001",
  "created_at": "2026-05-24T10:00:03Z"
}
```

触发场景：

- `MESSAGE_SEND_FAILED`
- `CONVERSATION_LOAD_FAILED`
- `BOT_STATUS_SYNC_FAILED`
- `RATE_LIMITED`
- `INTERNAL_ERROR`

说明：

- `error` 表示连接仍有效，但某个异步操作失败。
- `AUTH_EXPIRED` / `UNAUTHORIZED` 不通过普通 `error` 事件处理，应关闭 WebSocket 并回到登录态。

---

# 7. 数据模型

## 7.1 users

```sql
id
username
password_hash
employee_id
real_name
created_at
updated_at
```

## 7.2 bots

```sql
id
bot_id
owner_user_id
name
bot_type
token_hash
token_revealed_at
token_regenerated_at
connect_status
protocol_version
first_connected_at
last_seen_at
created_at
updated_at
revoked_at
```

字段枚举：

```text
bot_type: openclaw_assistant / custom_bot
connect_status: pending / authenticating / connected / disconnected / revoked
```

说明：

- `bots` 表只保存需要 Plugin 接入的外部 BOT，不保存系统级默认 BOT。
- `system_default_bot` 是系统内置身份，由 default-bot-service 管理。
- `token_revealed_at` 记录当前 token 明文是否已经展示过，`null` 表示仍可展示一次。
- `token_regenerated_at` 记录最近一次 token 重新生成时间。
- `bots.connect_status` 是最后一次持久化连接状态。
- 当前实时在线状态以 Redis `bot:online:{bot_id}` 为准。
- `bots` 表不保存绑定状态，绑定状态由 `user_bot_bindings.status` 作为唯一来源。

## 7.3 user_bot_bindings

```sql
id
user_id
bot_id
binding_type
status
created_at
revoked_at
```

字段枚举：

```text
binding_type: openclaw_assistant / custom_bot
status: active / revoked
```

`user_bot_bindings.status` 是绑定状态 source of truth。

## 7.4 bot_connection_logs

```sql
id
bot_id
event_type
trace_id
request_id
error_code
error_message
remote_addr
created_at
```

## 7.5 conversations

```sql
id
conversation_type
owner_user_id
target_type
target_id
last_message_id
last_message_at
created_at
updated_at
```

说明：

- 默认 BOT 会话：`conversation_type = system_bot`，`target_type = system_default_bot`，`target_id = default_bot`。
- 外部 BOT 会话：`conversation_type = bot`，`target_type = bot`，`target_id = bot_id`。
- P0 只要求会话壳字段可用。
- `last_message_id` 和 `last_message_at` 属于 P1 消息能力，用于会话列表高频查询，并作为 `conversation.updated` 事件字段来源。

## 7.6 messages

```sql
id
conversation_id
sender_type
sender_id
receiver_type
receiver_id
content_type
content
status
created_at
```

说明：`messages` 表属于 P1。P0 默认 BOT 命令结果不要求写入 `messages`。

---

# 8. BOT Gateway 协议

BOT Gateway 协议由 Plugin 文档定义：

```text
docs/plugin-npm-package.md
```

后端必须实现：

- `auth`
- `auth.result`
- `handshake`
- `handshake.result`
- `heartbeat`
- `heartbeat.result`
- `server.disconnect`

P1 基础单聊补充实现：

- `inbound_message`
- `outbound_message`
- `outbound_message.result`

## 8.1 连接状态同步

连接状态分层：

```text
MySQL bots.connect_status      最后一次持久化连接状态
Redis bot:online:{bot_id}      当前实时在线状态
```

更新规则：

- WebSocket 建连并开始鉴权：`connect_status = authenticating`
- handshake 成功：`connect_status = connected`，Redis 写入 `bot:online:{bot_id}`，设置 TTL
- heartbeat：刷新 Redis TTL，节流更新 `last_seen_at`
- `/disconnect {bot_id}`：关闭连接，删除 Redis 在线状态，`connect_status = disconnected`
- heartbeat 超时：Redis key 过期，后台任务或网关事件修正 MySQL 为 `disconnected`
- 服务启动：执行 startup cleanup，把 `connected/authenticating` 修正为 `disconnected`

P0 单实例 cleanup：

```sql
UPDATE bots
SET connect_status = 'disconnected'
WHERE connect_status IN ('connected', 'authenticating');
```

多实例部署时再增加 `gateway_instance_id`，只清理本实例负责的连接。

心跳与在线 TTL：

```text
Plugin heartbeat interval: 30s
Redis key: bot:online:{bot_id}
Redis TTL: 100s
离线判定阈值: 90s
```

说明：

- 每次收到 heartbeat 后刷新 Redis TTL。
- 90 秒未收到 heartbeat 后，服务端把 MySQL `connect_status` 修正为 `disconnected`。
- Redis TTL 设为 100 秒，用于覆盖调度延迟和网络抖动。

---

# 9. 安全要求

- token 明文只在 `/connect {bot_id}` 输出时展示。
- 数据库存储 token hash。
- P0 token 默认不过期，仅支持主动重新生成 / revoke。
- token 格式固定为 `ocb_live_` + 32 bytes secure random Base58。
- `TOKEN_EXPIRED` 为协议预留，P0 不启用自动过期。
- token 支持重新生成。
- `GET /api/bots/{bot_id}/connect-info` 是幂等读取，不自动重新生成 token，不使旧 token 失效。
- 如果 token 明文已经不可再展示，返回 masked token，并提示员工在默认 BOT 中二次确认。
- masked token 格式为 `ocb_live_****_{last4}`，如果 token 格式异常或无法取后 4 位，则返回 `[MASKED]`。
- connect-info 返回 `token_status`：`revealed_once` 或 `masked`。
- 默认 BOT 命令层复用 `/connect {bot_id}`，在员工二次确认后调用 `POST /api/bots/{bot_id}/connect-info/regenerate`。
- 主动重新生成 token 后，P0 固定为旧 token 立即失效。
- 如果该 BOT 当前已连接，服务端先下发 `server.disconnect`，再关闭旧 WebSocket。
- WebSocket close code 使用 `4001`，close reason 使用 `TOKEN_REGENERATED`。
- Plugin 日志和后端日志不能打印完整 token。
- BOT Gateway 必须支持 `wss://`。
- 单个 `bot_id` 默认只允许一个活跃连接。
- WebSocket 建连后 15 秒内未收到 `auth`，服务端以 close code `4000` / reason `AUTH_TIMEOUT` 关闭连接。
- P3 对 outbound message 做限流。
- 所有 BOT 操作必须校验 owner_user_id。

---

# 10. 后端验收标准

- [ ] 员工可以注册。
- [ ] 员工可以登录。
- [ ] JWT 使用 HS256，有效期 7 天。
- [ ] bcrypt rounds 为 12。
- [ ] `/connect {bot_id}` 的 `gateway_url` 来自 `BOT_GATEWAY_PUBLIC_URL`。
- [ ] 登录后自动具备默认 BOT 会话入口。
- [ ] `POST /api/default-bot/commands` 可执行默认 BOT 命令。
- [ ] `/help` 返回帮助。
- [ ] `/new-bot` 创建 `pending` BOT。
- [ ] `bot_id` 格式为 `bot_` + ULID。
- [ ] token 格式为 `ocb_live_` + 32 bytes secure random Base58。
- [ ] token 只存 hash。
- [ ] `/connect {bot_id}` 返回完整 Plugin 连接信息。
- [ ] 重复 `/connect {bot_id}` 不自动重新生成 token。
- [ ] token 已展示后再次 `/connect {bot_id}` 返回 masked token。
- [ ] 员工二次确认后 `/connect {bot_id}` 可触发 token 重新生成。
- [ ] confirm 输入错误时，默认 BOT 会重新提示正确确认文本。
- [ ] token 重新生成后，BOT Gateway 下发 `server.disconnect` 并使用 close code `4001` 关闭旧连接。
- [ ] 默认 BOT 不进入普通 `bots` 表。
- [ ] 默认 BOT 会话在注册后创建，登录时幂等补偿。
- [ ] BOT Gateway 能校验正确 `bot_id + token`。
- [ ] 错误 token 返回 `AUTH_FAILED`。
- [ ] handshake 成功后建立绑定。
- [ ] 心跳更新 `last_seen_at`。
- [ ] Redis `bot:online:{bot_id}` TTL 为 100 秒。
- [ ] BOT Gateway 建连后 15 秒未 auth 会关闭连接。
- [ ] 90 秒未收到心跳时标记 `disconnected`。
- [ ] 服务启动时 cleanup 修正历史 `connected/authenticating` 状态。
- [ ] 绑定状态只以 `user_bot_bindings.status` 为准。
- [ ] 连接日志包含 trace_id 和 request_id。

P1 后端验收：

- [ ] 员工 WebSocket 可下发 `message.new` 和 `bot.status_changed`。
- [ ] 员工消息能投递给 OpenClaw 员工助手。
- [ ] OpenClaw 员工助手回复能投递给员工。
- [ ] 历史消息可分页查询。

---

# 11. 第一版不做

- 主区 / 子区
- 文件上传下载
- 工单系统自动同步
- 多语言 Plugin SDK
- 复杂权限系统
- 多端登录冲突策略
- 2000 人压测自动化
