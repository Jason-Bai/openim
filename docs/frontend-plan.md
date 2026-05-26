# OpenClaw IM 前端方案（讨论版）

> 状态：方案讨论中，非最终版。
>
> 本文只描述 Web 前端。总方案见 `docs/overall-plan.md`，后端见 `docs/backend-plan.md`，Plugin 见 `docs/plugin-npm-package.md`。

---

# 1. 前端目标

第一版前端目标：

- 员工可以注册和登录。
- 员工登录后看到默认 BOT 会话。
- 员工可以在默认 BOT 中执行 `/help`、`/new-bot`、`/my-bots`、`/connect {bot_id}`、`/disconnect {bot_id}`、`/delete-bot {bot_id}`。
- 员工可以复制 `/connect {bot_id}` 输出的 Plugin 连接信息。
- 员工可以查看 OpenClaw 员工助手的连接状态。

P1 前端目标：

- 员工可以和已接入的 OpenClaw 员工助手进行基础单聊。
- 员工 WebSocket 断开后可自动重连。

---

# 2. 推荐技术栈

第一版直接推荐：

```text
language: TypeScript
framework: React
build: Vite
server state: TanStack Query
client state: Zustand
routing: React Router
ui: Ant Design
websocket: 原生 WebSocket 封装
```

推荐理由：

- React + Vite 适合快速搭建内部 Web IM 工具。
- TanStack Query 管理登录用户、BOT 列表、会话、历史消息等服务端状态。
- Zustand 管理当前会话、输入框、WebSocket 连接状态等客户端状态。
- Ant Design 的表单、列表、标签、弹窗、复制代码块组件成熟，适合第一版快速落地。

---

# 3. 前端运行配置

P0 开发环境：

```text
VITE_API_BASE_URL=/api
```

Vite proxy：

```text
/api -> http://localhost:8080
```

P1 员工 WebSocket 增加：

```text
VITE_WS_BASE_URL=ws://localhost:8080
```

说明：

- P0 所有 REST API 通过 `VITE_API_BASE_URL` 访问。
- P0 不依赖员工 WebSocket。
- P1 引入 `/ws` 后，前端从 `VITE_WS_BASE_URL` 拼接 WebSocket 地址。
- REST 返回 `UNAUTHORIZED` 时，前端清理 JWT 并回到登录页。
- P0 JWT 有效期由后端固定为 7 天，前端不做 refresh token。

---

# 4. 页面拆分

## 4.1 登录 / 注册页

能力：

- 注册账号
- 登录账号
- 保存登录态
- 登录失败提示

第一版字段：

```text
username
password
employee_id
real_name
```

## 4.2 主聊天页

布局：

```text
左侧：主菜单
中左：通讯录 / 会话列表
中间：聊天窗口
```

左侧主菜单：

```text
通讯录
事项（待开发）
总结（待开发）
应用（待开发）
```

P0 只展示并实现 `通讯录`。`事项`、`总结`、`应用` 在 P0 不展示，不做禁用入口。

通讯录分组：

```text
群聊
已添加的 AI
全部联系人
```

P0 通讯录包含：

- 已添加的 AI
  - 系统默认 BOT
  - 已接入的公司 OpenClaw 员工助手
- 全部联系人
  - 真人员工账号
  - 全部 BOT

说明：

- 第一版不做右侧 BOT 状态面板。
- 当前员工名下 BOT 状态通过默认 BOT 的 `/my-bots` 查看。
- `已添加的 AI` 是员工常用 / 已添加 BOT 的快捷分组。
- `全部联系人` 是完整联系人集合，包含真人员工和全部 BOT。
- P0 不在 `已添加的 AI` 列表展示状态标签。状态只通过默认 BOT 的 `/my-bots` 查看。
- 个人 BOT 不进入 P0 通讯录；P2 开启员工自建 BOT 后，再进入 `已添加的 AI` 和 `全部联系人`。

聊天窗口能力：

- 展示默认 BOT 命令回复
- 输入默认 BOT 命令
- `/connect {bot_id}` 返回的 JSON 连接信息使用 `CopyableCodeBlock` 展示并支持一键复制。

P1 增加：

- 展示历史消息
- 输入普通文本消息
- 发送消息
- 展示发送中 / 失败 / 已发送状态

## 4.3 默认 BOT 会话

默认 BOT 会话是员工接入 OpenClaw 员工助手的主要入口。

需要支持的交互：

- 输入 `/help`
- 输入 `/new-bot`
- 输入 `/my-bots`
- 输入 `/connect {bot_id}`
- 选择 bot_id
- 复制连接信息
- 输入 `/disconnect {bot_id}`
- 输入 `/delete-bot {bot_id}`

P0 默认 BOT 命令只通过文本输入完成，不做表单、按钮或可视化向导。

## 4.4 BOT 状态查看

第一版 BOT 状态不做独立右侧面板，通过默认 BOT 的 `/my-bots` 返回。

字段：

```text
bot_id
name
bot_type
connect_status
binding_status
last_seen_at
first_connected_at
```

状态展示：

```text
pending          等待连接
authenticating   鉴权中
connected        已连接
disconnected     已断开
revoked          已撤销
```

说明：

- `connect_status` 来自 BOT 连接状态。
- `binding_status` 是前端展示字段，由后端根据 `user_bot_bindings.status` 派生返回，不直接来自 `bots` 表。
- P0 不在 `已添加的 AI` 列表展示状态。P1/P2 如果增加状态标签，也只展示轻量状态，不承载完整管理操作。

---

# 5. 前端数据流

## 5.1 登录态

```text
登录成功
  ↓
保存 access_token
  ↓
拉取当前用户信息
  ↓
进入主聊天页
```

JWT 策略：

- P0 后端 JWT 有效期固定为 7 天。
- P0 不做 refresh token。
- 任意 REST 返回 `UNAUTHORIZED` 时，前端清理本地登录态并跳回登录页。

## 5.2 默认 BOT 命令

```text
员工输入命令
  ↓
前端调用 POST /api/default-bot/commands
  ↓
后端默认 BOT 命令系统处理
  ↓
后端返回默认 BOT 回复
  ↓
前端展示 BOT 回复
```

## 5.3 `/connect {bot_id}` 连接信息

前端需要把 `/connect {bot_id}` 返回的 JSON 用可复制代码块展示。

要求：

- 保持 JSON 格式。
- 一键复制。
- 不在日志或错误提示中泄露完整 token。
- 可以提示 token 敏感。
- 如果默认 BOT 返回 masked token，前端按普通 BOT 消息展示提示，不单独做按钮。
- masked token 标准格式为 `ocb_live_****_{last4}`；如果后端返回 `[MASKED]`，前端原样展示。
- 前端可根据 `token_status = masked` 展示“需要重新生成 token 才能查看明文”的提示。
- 员工需要重新生成 token 时，按默认 BOT 回复继续输入确认文本。
- 第一版确认文本由默认 BOT 明确给出，例如 `confirm regenerate bot_123`。
- 如果员工输入错误，默认 BOT 会重新提示正确确认文本。
- 如果员工输入 `cancel`，默认 BOT 取消本次 token 重新生成。
- 确认提示有效期为 5 分钟，过期后需要重新执行 `/connect {bot_id}`。
- 重新生成 token 后，默认 BOT 返回新的连接 JSON，前端继续使用同一个可复制代码块展示。

## 5.4 WebSocket（P1）

员工 WebSocket 属于 P1。P0 不依赖员工 WebSocket 完成默认 BOT 命令和 BOT 接入状态查看。

前端 WebSocket 只服务员工 Web 端。

不要和 Plugin / BOT Gateway WebSocket 混用。

职责：

- 接收新消息
- 接收 BOT 状态变化
- 接收连接断开 / 重连提示

重连策略：

- 登录后建立 `/ws` 连接。
- 断开后自动重连。
- 初始重连延迟 1s，最大 15s，指数退避。
- 页面可见时重连，页面隐藏时允许降频。
- 重连期间在聊天页显示轻量连接状态提示。
- 重连成功后重新拉取会话列表和当前会话最新消息，避免漏消息。
- 收到鉴权失败时停止重连并回到登录态。

error 事件处理：

- `retryable = true`：展示轻量错误提示；如果 `related_id` 是消息 ID，则把对应消息标记为发送失败并允许重试。
- `retryable = false`：展示错误提示，不自动重试。
- `AUTH_EXPIRED` / `UNAUTHORIZED` 不作为普通 `error` 处理，前端关闭 WebSocket 并回到登录态。

---

# 6. 前端模块

```text
src/
  api/
    auth.ts
    bots.ts
    conversations.ts
    defaultBot.ts
    messages.ts（P1）
  ws/
    webClient.ts（P1）
  pages/
    LoginPage.tsx
    ChatPage.tsx
  components/
    MainMenu.tsx
    ConversationList.tsx
    ContactList.tsx
    ChatWindow.tsx
    CommandInput.tsx
    MessageInput.tsx（P1）
    CopyableCodeBlock.tsx
  state/
    authStore.ts
    chatStore.ts
```

---

# 7. 前端验收标准

- [ ] 员工可以注册。
- [ ] 员工可以登录。
- [ ] 开发环境通过 Vite proxy 访问 `http://localhost:8080`。
- [ ] REST 返回 `UNAUTHORIZED` 时清理登录态并跳回登录页。
- [ ] 登录后进入聊天页。
- [ ] 会话列表出现默认 BOT。
- [ ] `/help` 可以展示帮助。
- [ ] `/new-bot` 后能看到新 bot_id。
- [ ] `/my-bots` 能看到 BOT 状态。
- [ ] `/connect {bot_id}` 返回的 JSON 可以一键复制。
- [ ] token 已展示后再次 `/connect {bot_id}` 可看到 masked token 和确认提示。
- [ ] 员工按默认 BOT 提示确认后，可以看到新 token 的连接 JSON。
- [ ] confirm 输入错误时，默认 BOT 会重新提示正确确认文本。
- [ ] masked token 按 `ocb_live_****_{last4}` 或 `[MASKED]` 原样展示。
- [ ] BOT 状态从 `pending` 更新为 `connected` 时前端可见。

P1 前端验收：

- [ ] 员工 WebSocket 收到 retryable error 时可以展示失败并允许重试。
- [ ] 员工 WebSocket 断开后可自动重连。
- [ ] 员工 WebSocket 重连成功后会刷新会话和当前消息。
- [ ] 员工可以给 OpenClaw 员工助手发消息。
- [ ] OpenClaw 员工助手回复后前端可见。

---

# 8. 第一版不做

- 复杂后台管理系统
- 可视化流程编排
- 富文本编辑器
- 文件上传
- 主区 / 子区 UI
- 移动端适配到完整体验
- 多主题
