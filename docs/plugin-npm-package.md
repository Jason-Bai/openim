# OpenClaw IM Bot Plugin npm Package 方案（讨论版）

> 状态：方案讨论中，非最终版。
>
> 本文是 `docs/overall-plan.md` 引用的 Plugin 独立方案，聚焦 OpenClaw 员工助手如何通过官方 npm package 接入本项目。

---

# 1. 目标

Plugin 的 P0 目标是让 OpenClaw 员工助手拿到默认 BOT `/connect {bot_id}` 输出的连接信息后，可以稳定接入 OpenClaw IM 服务端。

P0 需要屏蔽底层连接细节，包括：

- WebSocket 建连
- `bot_id + token` 鉴权
- 首条 handshake
- 心跳保活
- 断线重连
- 错误码处理
- 接入日志

P1 补充：

- 消息接收
- 消息发送

---

# 2. Package 定义

```text
package: @openim/openclaw-bot-plugin
status: 待开发
positioning: 本项目官方基础 SDK npm package
language: TypeScript
runtime: Node.js 18+
protocol: WebSocket JSON
target: OpenClaw 员工助手 / 后续员工自建 BOT
```

`@openim/openclaw-bot-plugin` 不是已有第三方包，而是本项目需要开发和维护的基础接入包。

第一版只要求支持 Node.js 运行环境。

浏览器、Deno、Python Bridge 暂不进入第一版范围。

---

# 3. 安装方式

P0 联调安装方式固定为本地 tarball，不发布到公开 npm。

Plugin 项目内打包：

```bash
cd packages/openclaw-bot-plugin
npm pack
```

OpenClaw 员工助手项目内安装：

```bash
npm install ./openim-openclaw-bot-plugin-0.1.0.tgz
```

P0 `/connect {bot_id}` 输出的 `plugin.install` 由后端配置生成，默认指向 tarball 安装命令或内部可访问的 tarball 地址。

P2/P3 再考虑公开 npm、私有 npm registry 和自动发布流程。

未来 npm package 发布后的安装命令：

```bash
npm install @openim/openclaw-bot-plugin
```

如果 OpenClaw 员工助手项目已经固定使用 `pnpm` 或 `yarn`，发布后可以使用等价安装命令：

```bash
pnpm add @openim/openclaw-bot-plugin
```

```bash
yarn add @openim/openclaw-bot-plugin
```

---

# 4. `/connect {bot_id}` 输出格式

默认 BOT 的 `/connect {bot_id}` 命令需要输出可复制的连接信息。

示例：

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

字段说明：

- `bot_id`：系统生成的 BOT 接入槽位 ID。
- `token`：该 BOT 的连接密钥，只展示一次，后续可重新生成。
- `gateway_url`：BOT Gateway WebSocket 地址。
- `protocol_version`：BOT 接入协议版本。
- `plugin.package`：官方 npm package 名称。
- `plugin.version`：P0 固定返回 `0.1.0`。
- `plugin.install`：安装命令，由后端配置生成；P0 默认使用 tarball 安装命令。
- `plugin.docs`：接入文档路径。
- token P0 默认不过期，仅支持主动重新生成 / revoke。

---

# 5. 最小接入代码

```ts
import { OpenClawBotClient } from "@openim/openclaw-bot-plugin";

const client = new OpenClawBotClient({
  botId: "bot_01HX7K9A2M4Q8R6T3ZP",
  token: "ocb_live_xxx",
  gatewayUrl: "wss://im.company.com/bot-gateway/ws",
  protocolVersion: "bot-v1"
});

await client.connect();
```

P0 最小接入只要求 `connect()` 成功并维持心跳。`onMessage` 和 `sendMessage` 跟随 P1 基础单聊一起落地。

P1 消息收发示例：

```ts
client.onMessage(async (message) => {
  await client.sendMessage({
    conversationId: message.conversationId,
    content: { type: "text", text: "收到" }
  });
});
```

---

# 6. Package API

## 6.1 Client Options

```ts
export type OpenClawBotClientOptions = {
  botId: string;
  token: string;
  gatewayUrl: string;
  protocolVersion?: "bot-v1";
  autoReconnect?: boolean;
  heartbeatIntervalMs?: number;
  logger?: BotPluginLogger;
};
```

默认值：

```text
protocolVersion: bot-v1
autoReconnect: true
heartbeatIntervalMs: 30000
```

## 6.2 Client

```ts
export class OpenClawBotClient {
  constructor(options: OpenClawBotClientOptions);

  connect(): Promise<void>;
  disconnect(): Promise<void>;

  onConnected(handler: () => void): void;
  onDisconnected(handler: (reason: DisconnectReason) => void): void;
  onError(handler: (error: BotPluginError) => void): void;

  // P1: 基础单聊
  onMessage(handler: (message: BotInboundMessage) => Promise<void> | void): void;
  sendMessage(input: SendMessageInput): Promise<SendMessageResult>;
}
```

## 6.3 Logger

```ts
export type BotPluginLogger = {
  debug?: (message: string, meta?: Record<string, unknown>) => void;
  info?: (message: string, meta?: Record<string, unknown>) => void;
  warn?: (message: string, meta?: Record<string, unknown>) => void;
  error?: (message: string, meta?: Record<string, unknown>) => void;
};
```

## 6.4 Types

```ts
export type DisconnectReason = {
  code:
    | "CLIENT_DISCONNECT"
    | "SERVER_DISCONNECT"
    | "NETWORK_ERROR"
    | "HEARTBEAT_TIMEOUT"
    | "AUTH_TIMEOUT"
    | "AUTH_FAILED"
    | "BOT_REVOKED"
    | "TOKEN_REGENERATED";
  message: string;
  retryable: boolean;
};
```

P1 消息类型：

```ts
export type BotInboundMessage = {
  messageId: string;
  conversationId: string;
  from: {
    type: "user" | "system";
    id: string;
  };
  content:
    | { type: "text"; text: string }
    | { type: "json"; data: unknown };
  createdAt: string;
  requestId: string;
};

export type SendMessageInput = {
  conversationId: string;
  content:
    | { type: "text"; text: string }
    | { type: "json"; data: unknown };
  requestId?: string;
};

export type SendMessageResult = {
  ok: boolean;
  messageId?: string;
  requestId: string;
  error?: BotPluginError;
};
```

字段映射规则：

- 协议层 JSON 使用 `snake_case`。
- SDK 对外 API 使用 `camelCase`。
- `request_id` 映射为 `requestId`。
- `message_id` 映射为 `messageId`。
- `conversation_id` 映射为 `conversationId`。
- `created_at` 映射为 `createdAt`。

---

# 7. WebSocket 协议

Plugin 和 BOT Gateway 使用 WebSocket JSON 消息。

所有消息都必须包含：

- `type`
- `request_id`
- `protocol_version`

服务端主动断开时，优先下发 `server.disconnect` 业务消息，然后关闭 WebSocket。

## 7.1 auth

Plugin 建连后首先发送鉴权消息。

```json
{
  "type": "auth",
  "request_id": "req_001",
  "protocol_version": "bot-v1",
  "bot_id": "bot_01HX7K9A2M4Q8R6T3ZP",
  "token": "ocb_live_xxx"
}
```

服务端返回：

```json
{
  "type": "auth.result",
  "request_id": "req_001",
  "protocol_version": "bot-v1",
  "ok": true
}
```

鉴权失败返回：

```json
{
  "type": "auth.result",
  "request_id": "req_001",
  "protocol_version": "bot-v1",
  "ok": false,
  "error": {
    "code": "AUTH_FAILED",
    "message": "bot_id or token is invalid",
    "retryable": false
  }
}
```

所有 `*.result` 消息遵循统一规则：

- `ok = true` 时不返回 `error`。
- `ok = false` 时必须返回 `error.code`、`error.message`、`error.retryable`。

## 7.2 handshake

鉴权成功后，Plugin 自动发送首条握手消息。

```json
{
  "type": "handshake",
  "request_id": "req_002",
  "protocol_version": "bot-v1",
  "bot_id": "bot_01HX7K9A2M4Q8R6T3ZP",
  "runtime": {
    "name": "openclaw-employee-assistant",
    "version": "1.0.0"
  }
}
```

服务端返回：

```json
{
  "type": "handshake.result",
  "request_id": "req_002",
  "protocol_version": "bot-v1",
  "ok": true,
  "binding_status": "bound"
}
```

握手失败返回：

```json
{
  "type": "handshake.result",
  "request_id": "req_002",
  "protocol_version": "bot-v1",
  "ok": false,
  "error": {
    "code": "HANDSHAKE_FAILED",
    "message": "runtime information is invalid",
    "retryable": false
  }
}
```

## 7.3 heartbeat

Plugin 默认每 30 秒发送心跳。

```json
{
  "type": "heartbeat",
  "request_id": "req_003",
  "protocol_version": "bot-v1",
  "bot_id": "bot_01HX7K9A2M4Q8R6T3ZP",
  "timestamp": 1716537600000
}
```

服务端返回：

```json
{
  "type": "heartbeat.result",
  "request_id": "req_003",
  "protocol_version": "bot-v1",
  "ok": true,
  "timestamp": 1716537600100
}
```

## 7.4 inbound_message（P1）

服务端向 Plugin 下发员工消息。

```json
{
  "type": "inbound_message",
  "request_id": "req_004",
  "protocol_version": "bot-v1",
  "message_id": "msg_001",
  "conversation_id": "conv_001",
  "from": {
    "type": "user",
    "id": "user_001"
  },
  "content": {
    "type": "text",
    "text": "你好"
  },
  "created_at": "2026-05-24T10:00:00Z"
}
```

Plugin 收到后触发 `onMessage`。

SDK 会将该协议消息转换为 `BotInboundMessage` 后传给 `onMessage`。

## 7.5 outbound_message（P1）

Plugin 向服务端发送 BOT 回复。

```json
{
  "type": "outbound_message",
  "request_id": "req_005",
  "protocol_version": "bot-v1",
  "bot_id": "bot_01HX7K9A2M4Q8R6T3ZP",
  "conversation_id": "conv_001",
  "content": {
    "type": "text",
    "text": "收到"
  }
}
```

服务端返回：

```json
{
  "type": "outbound_message.result",
  "request_id": "req_005",
  "protocol_version": "bot-v1",
  "ok": true,
  "message_id": "msg_002"
}
```

---

## 7.6 server.disconnect

服务端需要主动断开 Plugin 时，先下发结构化断开消息。

```json
{
  "type": "server.disconnect",
  "request_id": "req_server_001",
  "protocol_version": "bot-v1",
  "reason": {
    "code": "TOKEN_REGENERATED",
    "message": "token has been regenerated, please reconnect with the new token",
    "retryable": false
  }
}
```

随后服务端关闭 WebSocket：

```text
close code: 4001
close reason: TOKEN_REGENERATED
```

Plugin 处理规则：

- 如果收到 `server.disconnect`，以 `reason.code` 作为断开原因。
- 如果没有收到 `server.disconnect`，但 close code 是 `4001` 且 close reason 是 `TOKEN_REGENERATED`，也按 `TOKEN_REGENERATED` 处理。
- `TOKEN_REGENERATED` 不自动重连。

# 8. 状态机

```text
idle
  ↓ connect()
connecting
  ↓ websocket open
authenticating
  ↓ auth.result ok
handshaking
  ↓ handshake.result ok
connected
  ↓ disconnect() / close / heartbeat timeout
disconnected
  ↓ auto reconnect
connecting
```

失败状态：

```text
auth_failed
protocol_failed
revoked
network_error
```

---

# 9. 错误码

```text
AUTH_FAILED                  bot_id 或 token 错误
AUTH_TIMEOUT                 BOT Gateway 建连后未在 15 秒内发送 auth
TOKEN_EXPIRED                token 已过期，P0 不启用，作为后续协议预留
BOT_REVOKED                  BOT 已被删除或撤销
BOT_ALREADY_CONNECTED        同一个 bot_id 已存在活跃连接
PROTOCOL_VERSION_UNSUPPORTED 协议版本不支持
HANDSHAKE_FAILED             握手失败
HEARTBEAT_TIMEOUT            心跳超时
NETWORK_ERROR                网络错误
MESSAGE_FORMAT_INVALID       消息格式错误
RATE_LIMITED                 发送频率超限
INTERNAL_ERROR               服务端内部错误
```

Plugin 需要把服务端错误包装成统一异常：

```ts
export type BotPluginError = {
  code: string;
  message: string;
  requestId?: string;
  retryable: boolean;
  cause?: unknown;
};
```

---

# 10. 重连策略

默认开启自动重连。

P0 重连策略：

```text
初始延迟：1s
最大延迟：30s
退避方式：指数退避
抖动：需要
最大重试次数：无限
```

不应自动重连的错误：

- `AUTH_FAILED`
- `AUTH_TIMEOUT`
- `TOKEN_EXPIRED`
- `BOT_REVOKED`
- `PROTOCOL_VERSION_UNSUPPORTED`

会自动重连的错误：

- `NETWORK_ERROR`
- `HEARTBEAT_TIMEOUT`
- 服务端临时不可用

token 重新生成后的连接处理：

- 服务端先下发 `server.disconnect`，再主动关闭旧 WebSocket 连接。
- WebSocket close code 使用 `4001`，close reason 使用 `TOKEN_REGENERATED`。
- Plugin 触发 `onDisconnected({ code: "TOKEN_REGENERATED", retryable: false })`。
- Plugin 不自动重连，因为旧 token 已失效。
- OpenClaw 员工助手需要使用新的连接信息重新启动或重新配置。

auth 超时处理：

- Plugin 建连后立即发送 `auth`。
- 服务端 15 秒内未收到 `auth` 时关闭 WebSocket。
- WebSocket close code 使用 `4000`，close reason 使用 `AUTH_TIMEOUT`。
- Plugin 触发 `onDisconnected({ code: "AUTH_TIMEOUT", retryable: false })`。

---

# 11. 安全要求

- token 只用于 BOT Gateway 鉴权。
- 服务端只存储 token hash，不存明文 token。
- `/connect {bot_id}` 返回 token 时需要提示员工妥善保存。
- P0 token 默认不过期，仅支持主动重新生成 / revoke。
- `TOKEN_EXPIRED` 为协议预留，P0 不启用自动过期。
- `/connect {bot_id}` 默认是幂等读取，不自动重新生成 token，不使旧 token 失效。
- 如果 token 明文已经不可再展示，服务端返回 masked token，并提示员工在默认 BOT 中二次确认。
- masked token 格式为 `ocb_live_****_{last4}`，如果 token 格式异常或无法取后 4 位，则返回 `[MASKED]`。
- connect-info 返回 `token_status`：`revealed_once` 或 `masked`。
- 员工在默认 BOT 中二次确认后，服务端主动重新生成 token。
- 主动重新生成 token 后，P0 固定为旧 token 立即失效。
- token 泄露后可以重新生成。
- Plugin 日志默认不能打印完整 token。
- WebSocket 必须使用 `wss://`。
- 服务端需要限制单个 `bot_id` 的并发连接数量。
- P3 对 outbound message 做频率限制。

---

# 12. 可验证验收标准

- [ ] npm package 可以通过 `npm pack` tarball 被 Node.js 18 项目安装。
- [ ] TypeScript 类型可用。
- [ ] 给定正确 `bot_id + token`，Plugin 可以连接 BOT Gateway。
- [ ] token 错误时返回 `AUTH_FAILED`。
- [ ] 鉴权成功后自动发送 handshake。
- [ ] handshake 成功后服务端建立绑定。
- [ ] Plugin 每 30 秒发送 heartbeat。
- [ ] 服务端 90 秒未收到 heartbeat 时标记 BOT 离线。
- [ ] 断线后 Plugin 自动重连。
- [ ] token 重新生成后，旧连接收到 `TOKEN_REGENERATED` 并停止自动重连。
- [ ] 所有请求都有 `request_id`。
- [ ] 日志中不出现完整 token。

P1 Plugin 验收：

- [ ] 收到 `inbound_message` 时触发 `onMessage`。
- [ ] 调用 `sendMessage` 后服务端收到 `outbound_message`。

---

# 13. 第一版不做

- 浏览器端 Plugin
- Python SDK
- Deno SDK
- 多语言 SDK
- Plugin 自动发布流程
- 插件市场
- 复杂富文本消息
- 文件消息
- 群聊 / 主区 / 子区消息

这些能力可以在 P1/P2/P3 阶段补充。
