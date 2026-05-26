# OpenClaw IM 任务拆解

> 状态：草稿。基于 `overall-plan.md` / `backend-plan.md` / `frontend-plan.md` / `plugin-npm-package.md` 拆解。
>
> 人天为单人估算，不含联调和测试返工缓冲。优先级列含阶段（P0-Gate、P0-A/B/C、P1、P2、P3）。`领域` 用于汇总和排期分工。

---

## P0-Gate：启动前置确认

这些是 P0 启动前置条件，不计入研发人天，但会影响 P0 是否能按当前方案开工。

| # | 名称 | 简述 | 优先级 | 领域 | 依赖项 | 人天 |
|---|------|------|--------|------|--------|------|
| G1 | 确认 OpenClaw 运行环境 | 确认 OpenClaw 员工助手支持 Node.js 18+，可安装并运行 `@openim/openclaw-bot-plugin` | P0-Gate | Product/Tech | — | 0d |
| G2 | 确认工单接入方式 | 确认第一版不做工单系统自动同步，员工人工复制默认 BOT 输出的连接信息给 OpenClaw 员工助手 | P0-Gate | Product | — | 0d |
| G3 | 确认 Plugin 联调安装方式 | P0 不发布公开 npm，固定使用 `npm pack` tarball 安装；公开 npm / 私有 registry 后移 | P0-Gate | Product/Tech | G1 | 0d |
| G4 | 确认对外 Gateway 地址 | 后端通过 `BOT_GATEWAY_PUBLIC_URL` 生成 `/connect {bot_id}` 的 `gateway_url`，不从 request host 推导 | P0-Gate | Tech/Ops | — | 0d |
| G5 | 确认 JWT 策略 | P0 固定 HS256、`JWT_SECRET` 环境变量、有效期 7 天、不做 refresh token | P0-Gate | Tech/Security | — | 0d |

---

## P0-A：系统级初始化与员工账号

目标：员工可以进入系统，看到系统默认 BOT，并能查看真人员工通讯录。

| # | 名称 | 简述 | 优先级 | 领域 | 依赖项 | 人天 |
|---|------|------|--------|------|--------|------|
| 0 | 本地开发环境 | `docker-compose.yml` 启动 MySQL 8 + Redis，提供 `.env.example`，后端默认连接本地服务 | P0-A | DevOps | G1, G2, G3, G4, G5 | 0.5d |
| 1 | 后端项目初始化 | FastAPI + Uvicorn + Pydantic v2 脚手架、SQLAlchemy 2.x、Alembic、MySQL、Redis 依赖配置、统一 Response 结构、统一错误码、HTTP 状态码映射、`BOT_GATEWAY_PUBLIC_URL` / JWT 配置读取 | P0-A | Backend | #0 | 0.75d |
| 2 | 数据库基础 schema | `users`、`conversations` 表 Alembic 迁移脚本，含默认 BOT 会话所需字段 | P0-A | Backend | #1 | 0.5d |
| 3 | 用户注册接口 | `POST /api/auth/register`，密码 bcrypt 哈希，注册后触发默认 BOT 会话初始化 | P0-A | Backend | #2 | 1.5d |
| 4 | 用户登录接口 | `POST /api/auth/login`，签发 HS256 JWT，有效期 7 天，登录时幂等执行 `ensureDefaultBotConversation` | P0-A | Backend | #3 | 1d |
| 5 | 当前用户接口 | `GET /api/auth/me`，JWT 解析拦截器，当前用户注入 | P0-A | Backend | #4 | 0.5d |
| 6 | 默认 BOT 服务初始化 | 定义 `system_default_bot` 系统身份，不进 `bots` 表；提供 `ensureDefaultBotConversation` 幂等方法和 `GET /api/conversations` 基础会话壳 | P0-A | Backend | #2 | 1d |
| 7 | 默认 BOT 命令框架 | 命令路由、Handler 接口、消息生成机制、`/` 前缀解析、`POST /api/default-bot/commands` 请求 / 响应通道 | P0-A | Backend | #6 | 1.5d |
| 8 | `/help` 命令 | 返回所有命令说明的稳定帮助文本 | P0-A | Backend | #7 | 0.5d |
| 9 | 员工列表接口 | `GET /api/users`，返回系统内所有员工账号（id/username/employee_id/real_name），不返回敏感字段，需 JWT 鉴权 | P0-A | Backend | #5 | 0.5d |
| 10 | 前端项目初始化 | Vite + React + TypeScript + React Router + TanStack Query + Zustand + Ant Design，目录结构，`VITE_API_BASE_URL` 与 Vite proxy 配置 | P0-A | Frontend | #0 | 0.5d |
| 11 | 登录 / 注册页 | 注册表单（username/password/employee_id/real_name）、登录表单、JWT 持久化、失败提示 | P0-A | Frontend | #3, #4, #10 | 1.5d |
| 12 | 主聊天页基础布局 | 主菜单 + 通讯录/会话列表 + 聊天窗口，路由守卫，退出登录 | P0-A | Frontend | #5, #10 | 2d |
| 13 | 默认 BOT 会话入口展示 | 「已添加的 AI」分组，默认 BOT 出现在会话列表，可点击进入聊天窗口 | P0-A | Frontend | #6, #12 | 1d |
| 14 | 通讯录联系人列表展示 | 「全部联系人」分组展示真人员工账号（来自 `GET /api/users`）和系统默认 BOT；外部 BOT 接入后由 P0-B 补充展示 | P0-A | Frontend | #9, #12 | 1d |
| 15 | `/help` 前端展示 | 聊天窗口输入 `/help`，收到默认 BOT 回复后正常展示文本 | P0-A | Frontend | #8, #13 | 0.5d |

**P0-A 小计：Backend 7.75d，Frontend 6.5d，DevOps 0.5d，合计 14.75d**

---

## P0-B：OpenClaw 员工助手接入

目标：员工通过默认 BOT 创建接入槽位，OpenClaw 员工助手通过 Plugin 接入系统。

| # | 名称 | 简述 | 优先级 | 领域 | 依赖项 | 人天 |
|---|------|------|--------|------|--------|------|
| 16 | BOT 相关 schema | `bots`（含 `bot_type`、`token_revealed_at`、`token_regenerated_at`）、`user_bot_bindings`、`bot_connection_logs` Alembic 迁移 | P0-B | Backend | #1 | 1d |
| 17 | token 生成与 hash 存储 | 生成 `ocb_live_` + 32 bytes secure random Base58 token，数据库只存 bcrypt hash，支持 masked 格式 `ocb_live_****_{last4}` 和 `[MASKED]` | P0-B | Backend | #16 | 1d |
| 18 | `/new-bot` 命令 | 创建 `pending` 状态 BOT 接入槽位，生成 `bot_` + ULID 格式 `bot_id`，返回 bot_id 和槽位基本信息；不返回 token，token 通过 `/connect {bot_id}` 获取 | P0-B | Backend | #7, #16, #17 | 1d |
| 19 | `/connect {bot_id}` 幂等读取 | `GET /api/bots/{bot_id}/connect-info`；`gateway_url` 来自 `BOT_GATEWAY_PUBLIC_URL`；token 未展示则写 `token_revealed_at` 返回明文；已展示则返回 masked + `token_status: masked` | P0-B | Backend | #17, #18 | 1.5d |
| 20 | token 重新生成 pending_action 流程 | Redis key `bot:pending_action:{user_id}:{bot_id}`，TTL 5min；提示 `confirm regenerate {bot_id}`；处理 confirm/cancel/错误输入/超时 | P0-B | Backend | #19 | 2d |
| 21 | token 重新生成接口 | `POST /api/bots/{bot_id}/connect-info/regenerate`；新 token 生成，旧 token 立即失效；返回新连接信息 | P0-B | Backend | #20 | 1d |
| 22 | `/my-bots` 命令 | 查询当前员工名下 BOT 列表，返回 bot_id/name/bot_type/connect_status/binding_status/last_seen_at | P0-B | Backend | #16 | 0.5d |
| 23 | `/disconnect {bot_id}` 命令 | 主动断开指定 BOT 当前连接，不撤销绑定，不使 token 失效 | P0-B | Backend | #7, #16 | 0.5d |
| 24 | `/delete-bot {bot_id}` 命令 | 删除未使用或已断开的 BOT 槽位，校验 owner_user_id | P0-B | Backend | #16 | 0.5d |
| 25 | BOT Gateway WebSocket 基础 | `wss://.../bot-gateway/ws`，FastAPI WebSocket，独立于员工 `/ws`，连接管理，Session 注册，建连后 15 秒内未 auth 则以 `4000/AUTH_TIMEOUT` 关闭 | P0-B | Backend | #1 | 1.5d |
| 26 | auth / auth.result 处理 | 接收 `auth` 消息，校验 `bot_id + token hash`，返回 `auth.result`（ok/fail + AUTH_FAILED），更新 `connect_status = authenticating` | P0-B | Backend | #17, #25 | 1d |
| 27 | handshake / handshake.result 处理 | 接收 `handshake`，记录 runtime，返回 `handshake.result`，`connect_status = connected`，写 Redis `bot:online:{bot_id}`，TTL 100 秒 | P0-B | Backend | #26 | 1d |
| 28 | 绑定服务 | handshake 成功后写 `user_bot_bindings`（active），处理解绑，保留审计记录 | P0-B | Backend | #27, #16 | 1d |
| 29 | heartbeat 基础处理 | 接收 `heartbeat`，返回 `heartbeat.result`，刷新 Redis TTL，节流更新 `last_seen_at` | P0-B | Backend | #27 | 1d |
| 30 | server.disconnect + close code 4001 | token 重新生成时先下发 `server.disconnect`，再以 close code `4001` / `TOKEN_REGENERATED` 关闭旧连接 | P0-B | Backend | #25, #21 | 0.5d |
| 31 | 单 bot_id 并发连接限制 | BOT_ALREADY_CONNECTED 错误码，拒绝同一 bot_id 第二个活跃连接 | P0-B | Backend | #25 | 0.5d |
| 32 | Plugin npm 包初始化 | tsup 配置，ESM + CJS 双产物，TypeScript 严格模式，package.json，types 导出，`npm pack` tarball 联调安装 | P0-B | Plugin | G1, G3 | 1d |
| 33 | Plugin WebSocket 建连 + auth | 连接 gateway_url，发送 `auth` 消息（bot_id + token + protocol_version + request_id），等待 `auth.result` | P0-B | Plugin | #25, #26, #32 | 1.5d |
| 34 | Plugin handshake | `auth.result ok` 后自动发送 `handshake`（含 runtime），等待 `handshake.result` | P0-B | Plugin | #27, #33 | 0.5d |
| 35 | Plugin heartbeat | 每 30s 发送 `heartbeat`，接收 `heartbeat.result`，响应超时记录 | P0-B | Plugin | #29, #34 | 0.5d |
| 36 | Plugin 状态机 | idle → connecting → authenticating → handshaking → connected → disconnected；失败态：auth_failed/revoked/network_error | P0-B | Plugin | #34 | 1d |
| 37 | Plugin 断线重连 | 指数退避（1s→30s）+ jitter，最大重试次数无限，非重连错误不重试（AUTH_FAILED/BOT_REVOKED 等） | P0-B | Plugin | #36 | 1d |
| 38 | Plugin 错误处理与类型导出 | BotPluginError、DisconnectReason、BotPluginLogger；token 日志脱敏 | P0-B | Plugin | #32 | 1d |
| 39 | Plugin TOKEN_REGENERATED 处理 | 收到 `server.disconnect` 或 close code 4001 时触发 `onDisconnected({ code: TOKEN_REGENERATED, retryable: false })`，不自动重连 | P0-B | Plugin | #37, #30 | 0.5d |
| 40 | 前端 `/new-bot` 命令入口 | 聊天窗口可输入 `/new-bot`，展示 BOT 创建结果（bot_id 和槽位信息） | P0-B | Frontend | #18, #13 | 0.5d |
| 41 | 前端 `/connect {bot_id}` + CopyableCodeBlock | 展示连接 JSON 代码块，一键复制；展示 masked token、`token_status` 和 confirm 确认流程 | P0-B | Frontend | #19, #20, #13 | 2d |
| 42 | 前端 `/my-bots` 展示与联系人刷新 | 展示 BOT 状态列表（pending/authenticating/connected/disconnected/revoked）；已接入的公司 OpenClaw 员工助手进入「已添加的 AI」和「全部联系人」 | P0-B | Frontend | #22, #13, #14 | 1d |

**P0-B 小计：Backend 15.5d，Plugin 7d，Frontend 3.5d，合计 26d**

---

## P0-C：可验证与可排查

目标：接入失败时能定位原因。

| # | 名称 | 简述 | 优先级 | 领域 | 依赖项 | 人天 |
|---|------|------|--------|------|--------|------|
| 43 | heartbeat 超时修正 | 90s 未收到 heartbeat 后标记 `disconnected`，修正 Redis/MySQL 状态 | P0-C | Backend | #29 | 0.5d |
| 44 | 连接日志服务 | 写 `bot_connection_logs`，包含 event_type/trace_id/request_id/error_code/remote_addr | P0-C | Backend | #16 | 1d |
| 45 | request_id 全链路 | 所有 WebSocket 消息和 REST 响应携带 request_id；日志输出 request_id | P0-C | Backend | #25 | 0.5d |
| 46 | 服务启动 cleanup | 启动时执行 SQL 把 `connected/authenticating` 修正为 `disconnected`（单实例版） | P0-C | Backend | #16 | 0.5d |
| 47 | token 日志脱敏 | 后端所有日志禁止打印完整 token，包含 filter/interceptor 层 | P0-C | Backend | #17 | 0.5d |
| 48 | 错误码文档与实现对齐 | 确认 AUTH_FAILED/BOT_REVOKED/HEARTBEAT_TIMEOUT 等错误码在 Gateway 和 Plugin 中对齐 | P0-C | Backend | #26, #38 | 0.5d |

**P0-C 小计：Backend 3.5d，合计 3.5d**

---

## P1：基础 IM

目标：员工与 OpenClaw 员工助手可以单聊。

| # | 名称 | 简述 | 优先级 | 领域 | 依赖项 | 人天 |
|---|------|------|--------|------|--------|------|
| 49 | messages schema | `messages` 表（含 sender_type/content_type/content/status）Alembic 迁移，`conversations` 表补 last_message_id/last_message_at | P1 | Backend | #1 | 0.5d |
| 50 | 消息发送接口 | `POST /api/messages`，保存消息，投递给 BOT Gateway（inbound_message） | P1 | Backend | #49, #25 | 1.5d |
| 51 | 历史消息接口 | `GET /api/conversations/{id}/messages`，分页，保证稳定排序 | P1 | Backend | #49 | 1d |
| 52 | 会话列表消息字段增强 | `GET /api/conversations` 增加 last_message/last_message_at 等消息字段 | P1 | Backend | #49 | 0.5d |
| 53 | 员工 WebSocket `/ws` | 建连、JWT 鉴权、Session 管理，与 BOT Gateway 完全隔离 | P1 | Backend | #1 | 2d |
| 54 | 下发 message.new | BOT outbound_message 到达后，通过员工 WebSocket 推 `message.new` | P1 | Backend | #53, #38 | 1d |
| 55 | 下发 message.status | 消息发送成功/失败后推 `message.status`（sent/failed） | P1 | Backend | #53, #50 | 0.5d |
| 56 | 下发 bot.status_changed | BOT connect_status 变化时通过员工 WebSocket 推送 | P1 | Backend | #53, #27 | 0.5d |
| 57 | 下发 conversation.updated | 消息落库后推 `conversation.updated`（含 last_message_id） | P1 | Backend | #53, #50 | 0.5d |
| 58 | 员工 WebSocket error 事件 | retryable=true 展示轻量提示；retryable=false 不重试；AUTH_EXPIRED 关闭连接回到登录态 | P1 | Backend | #53 | 0.5d |
| 59 | Plugin onMessage / sendMessage | 导出 BotInboundMessage、SendMessageInput、SendMessageResult；接收 `inbound_message` → 转换 BotInboundMessage（snake_case 到 camelCase）→ 触发回调；sendMessage 发 `outbound_message`，等待 `outbound_message.result` | P1 | Plugin | #34, #50 | 1d |
| 60 | 前端 WebSocket 重连策略 | 登录后建连，断开后指数退避重连（1s→15s），重连成功后重新拉取会话和当前消息 | P1 | Frontend | #53 | 1d |
| 61 | 前端聊天窗口消息展示 | 展示历史消息，滚动加载，区分 user/bot sender 气泡样式 | P1 | Frontend | #51, #12 | 2d |
| 62 | 前端消息输入与发送 | MessageInput 组件，发送状态（发送中/已发送/失败+重试） | P1 | Frontend | #50, #61 | 1.5d |
| 63 | 前端 WebSocket 接入 | webClient.ts，接收 message.new/bot.status_changed/error，触发 Zustand 状态更新 | P1 | Frontend | #53, #58, #60 | 2d |
| 64 | 前端 BOT 状态实时更新 | 接收 bot.status_changed 后，会话列表和聊天窗口 BOT 状态实时刷新 | P1 | Frontend | #63, #56 | 1d |

**P1 小计：Backend 8.5d，Frontend 7.5d，Plugin 1d，合计 17d**

---

## P2：员工自建 BOT

目标：员工自己的 BOT 复用已走通的接入链路。

| # | 名称 | 简述 | 优先级 | 领域 | 依赖项 | 人天 |
|---|------|------|--------|------|--------|------|
| 65 | 自定义 BOT 名称 | `/new-bot [name]` 支持可选名称参数，`GET /api/bots` 返回 name 字段 | P2 | Backend | #18 | 0.5d |
| 66 | 多 BOT 管理 | 同一员工可创建多个 BOT，`/my-bots` 展示完整列表，`/delete-bot` 支持多 BOT 清理 | P2 | Backend | #22, #24 | 1d |
| 67 | 前端自建 BOT 区分展示 | 通讯录区分 openclaw_assistant 和 custom_bot 类型，个人 BOT 进入「已添加的 AI」和「全部联系人」 | P2 | Frontend | #66, #42 | 1d |

**P2 小计：Backend 1.5d，Frontend 1d，合计 2.5d**

---

## P3：扩展 IM 与运维

目标：完善公司 IM 能力和上线运行能力。

| # | 名称 | 简述 | 优先级 | 领域 | 依赖项 | 人天 |
|---|------|------|--------|------|--------|------|
| 68 | Redis 实时在线状态完善 | bot:online:{bot_id} TTL 机制、后台任务修正 MySQL、多实例 gateway_instance_id 支持 | P3 | Backend | #43 | 2d |
| 69 | outbound message 限流 | 单 bot_id 发送频率限制，RATE_LIMITED 错误码返回 | P3 | Backend | #50 | 1d |
| 70 | MinIO 文件存储预留 | 接入 MinIO，文件上传下载接口骨架（不上前端） | P3 | Backend | #1 | 2d |
| 71 | 主区 / 子区消息 | 群聊 conversation_type 扩展，消息模型扩展 | P3 | Backend | #49 | 5d |
| 72 | 监控与告警 | Prometheus + Grafana 指标，关键指标告警（连接数/延迟/错误率） | P3 | DevOps | — | 3d |
| 73 | 2000 人压测 | 压测脚本，BOT Gateway 并发连接压测，消息吞吐压测 | P3 | QA/DevOps | #68, #69 | 3d |
| 74 | 部署脚本 | Docker Compose / K8s Helm Chart，环境变量管理，CI/CD 骨架 | P3 | DevOps | — | 3d |

**P3 小计：Backend 10d，DevOps/QA 9d，合计 19d**

---

## 汇总

| 阶段 | Backend | Frontend | Plugin | DevOps/QA | 小计 |
|------|---------|----------|--------|-----------|------|
| P0-Gate | — | — | — | — | 0d |
| P0-A | 7.75d | 6.5d | — | 0.5d | 14.75d |
| P0-B | 15.5d | 3.5d | 7d | — | 26d |
| P0-C | 3.5d | — | — | — | 3.5d |
| P1 | 8.5d | 7.5d | 1d | — | 17d |
| P2 | 1.5d | 1d | — | — | 2.5d |
| P3 | 10d | — | — | 9d | 19d |
| **总计** | **46.75d** | **18.5d** | **8d** | **9.5d** | **82.75d** |

> P0（Gate + A+B+C）= 44.25d，其中研发人天为 44.25d，Gate 不计研发人天。
>
> 人天为单人串行估算。如后端/前端/Plugin 并行开发，P0 实际日历时间可压缩至 3～4 周（3 人并行），但仍需预留联调和返工缓冲。
