# 前端 UI 修正技术设计

**日期：** 2026-06-10  
**作者：** AI Code Review  
**状态：** 待评审

---

## 背景

对 `apps/web` 前端界面进行 UI 审查，发现若干结构性问题、视觉品质问题和细节缺陷。本文档记录各问题的技术分析及对应修复方案，供工程团队实施参考。

---

## 影响范围

| 文件 | 修改类型 |
|------|---------|
| `apps/web/src/styles.css` | 主要修改（布局、气泡、颜色变量） |
| `apps/web/src/pages/App.tsx` | 结构调整（导航、Header、气泡） |
| `apps/web/src/components/CopyableCodeBlock.tsx` | 无需修改 |
| `apps/web/index.html` | 添加 Google Fonts 引用 |

---

## P0 — 结构性问题

### P0-1：三列固定宽度布局在中等屏幕不可用

**问题描述：**

`.shell` 使用 `grid-template-columns: 168px 320px 1fr`，左侧两栏固定占用 488px。在 860–1100px 宽度的屏幕（主流笔记本分辨率区间）上，聊天区域被严重压缩至不足 200px，响应式断点仅有一个 `@media (max-width: 860px)`，触发后直接切换为单列堆叠，缺乏平板/窄屏幕的中间态布局。

**修复方案：**

将左侧导航改为 56px 图标栏（见 P0-2），中间联系人栏缩窄至 260px，并增加中间断点：

```css
.shell {
  height: 100vh;
  display: grid;
  grid-template-columns: 56px 260px 1fr;
  overflow: hidden;
}

@media (max-width: 1000px) {
  .shell { grid-template-columns: 56px 220px 1fr; }
}

@media (max-width: 720px) {
  .shell {
    grid-template-columns: 1fr;
    grid-template-rows: 52px auto 1fr;
  }
}
```

**验证：** 在 768px、1024px、1440px 宽度下分别截图，确认聊天区域可用宽度不低于 400px。

---

### P0-2：左侧导航宽 168px 但内容稀少，浪费空间

**问题描述：**

左侧导航栏宽 168px，实际只放了 2 个按钮和账户信息，大量空白。按钮选中状态使用 Ant Design `type="primary"`（蓝色），在深色 `#152033` 背景上视觉突兀。

**修复方案：**

改为 **56px 图标栏**，按钮仅显示图标，悬浮显示 Tooltip。

**CSS 改动：**

```css
.mainMenu {
  width: 56px;
  background: #111c2d;
  padding: 12px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.brand {
  width: 36px;
  height: 36px;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 800;
  color: #fff;
}

.navItem {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8da3bf;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.navItem:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.navItem.active {
  background: rgba(22, 104, 220, 0.25);
  color: #6eb3ff;
}

.accountFooter {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding-top: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  width: 100%;
}
```

**TSX 改动（`App.tsx` ChatPage 中的 aside.mainMenu）：**

```tsx
<aside className="mainMenu">
  <div className="brand">IM</div>
  <nav style={{ display: 'flex', flexDirection: 'column', gap: 4, width: '100%', alignItems: 'center' }}>
    <Tooltip title="会话" placement="right">
      <div
        className={`navItem ${menu === 'sessions' ? 'active' : ''}`}
        onClick={() => { setMenu('sessions'); ... }}
      >
        <MessagesSquare size={20} />
      </div>
    </Tooltip>
    <Tooltip title="通讯录" placement="right">
      <div
        className={`navItem ${menu === 'contacts' ? 'active' : ''}`}
        onClick={() => { setMenu('contacts'); ... }}
      >
        <Users size={20} />
      </div>
    </Tooltip>
  </nav>
  <div className="menuSpacer" />
  <div className="accountFooter">
    <Tooltip title={username} placement="right">
      <div className="navItem" style={{ fontSize: 12, fontWeight: 700, color: '#8da3bf' }}>
        {username.slice(0, 2).toUpperCase()}
      </div>
    </Tooltip>
    <Tooltip title="退出" placement="right">
      <div className="navItem" onClick={onLogout}>
        <LogOut size={16} />
      </div>
    </Tooltip>
  </div>
</aside>
```

**注意：** `Tooltip` 从 `antd` 导入，`MessagesSquare`、`Users` 从 `lucide-react` 导入（替换当前使用的 `UsersRound`）。

---

## P1 — 视觉品质问题

### P1-1：聊天气泡圆角缺乏方向感

**问题描述：**

当前用户气泡和机器人气泡 `border-radius` 完全一样（`8px`），缺乏现代 IM 的方向感设计。

**修复方案：**

```css
/* 通用气泡基础样式 */
.bubble {
  max-width: min(540px, 72%);
  white-space: pre-wrap;
  padding: 10px 14px;
  line-height: 1.6;
  font-size: 14px;
  border: none;
}

/* 机器人/系统消息（左侧对齐） */
.message.bot .bubble {
  background: #f0f4fa;
  color: #172033;
  border-radius: 4px 16px 16px 16px;
}

/* 用户消息（右侧对齐） */
.message.user .bubble {
  background: #1668dc;
  color: #fff;
  border-radius: 16px 4px 16px 16px;
}
```

---

### P1-2：聊天 Header 高度 76px 但内容单薄

**问题描述：**

`.chatHeader` 高度 76px 仅显示标题和 `target_id`，`target_id` 是后端的内部 ID 字符串，对用户无意义。现有数据中已有 `online` 字段，但未在 Header 展示。

**修复方案：**

**CSS：**
```css
.chatHeader {
  height: 60px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  background: #fff;
  border-bottom: 1px solid #e5e9f2;
  flex-shrink: 0;
}

.chatTitle {
  font-size: 15px;
  font-weight: 600;
  color: #172033;
  line-height: 1.3;
}

.chatStatus {
  font-size: 12px;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 4px;
  line-height: 1;
}
```

**TSX（`ConversationChat` 组件 header 部分）：**

```tsx
<header className="chatHeader">
  <div>
    <div className="chatTitle">{conversation.title}</div>
    <div className="chatStatus">
      {conversation.online
        ? <><span className="onlineDot" style={{ width: 6, height: 6 }} /> 在线</>
        : '离线'
      }
    </div>
  </div>
</header>
```

---

### P1-3：登录页视觉单薄

**问题描述：**

登录页背景 `#f5f7fb`（浅灰白），卡片为纯白，整体视觉平淡，无品牌存在感，无入场动效。

**修复方案：**

**CSS：**
```css
.loginPage {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: linear-gradient(145deg, #0d1b2a 0%, #152033 55%, #1a2d44 100%);
}

.loginPanel {
  width: min(400px, 100%);
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.10);
  border-radius: 16px;
  padding: 36px 32px;
  backdrop-filter: blur(24px);
  display: grid;
  gap: 20px;
  box-shadow: 0 32px 80px rgba(0, 0, 0, 0.5);
}

.loginLogo {
  text-align: center;
  font-size: 26px;
  font-weight: 800;
  color: #fff;
  letter-spacing: -0.5px;
}
```

**TSX（`LoginPage` 组件）：**

将 `<Typography.Title level={2}>OpenIM</Typography.Title>` 替换为：

```tsx
<div className="loginLogo">OpenIM</div>
```

Ant Design `ConfigProvider` 需增加 dark token 覆盖以确保表单元素在深色背景上可读：

```tsx
// main.tsx
<ConfigProvider
  locale={zhCN}
  theme={{
    algorithm: theme.darkAlgorithm,
    token: { colorBgContainer: 'transparent', colorBorder: 'rgba(255,255,255,0.15)' }
  }}
>
```

> [!WARNING]
> `theme.darkAlgorithm` 会影响全局 Ant Design 组件样式。若只想登录页使用深色，需在 `LoginPage` 内单独包裹一层 `<ConfigProvider theme={{ algorithm: theme.darkAlgorithm }}>`，而不改动 `main.tsx`。

---

## P2 — 细节改进

### P2-1：联系人图标缺乏色彩区分

**问题描述：**

Bot 图标和 User 图标同为灰色 `#526173`，在快速扫描时无法区分类型。

**修复方案：**

```css
.contactIcon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
}

.contactIcon.bot  { background: #e6f0ff; color: #1668dc; }
.contactIcon.user { background: #e8f7ef; color: #20b26b; }
```

**TSX（`ContactLine` 组件）：**

```tsx
<div className={`contactIcon ${icon}`}>
  {icon === 'bot' ? <Bot size={15} /> : <UserRound size={15} />}
</div>
```

---

### P2-2：快捷指令样式改进

**问题描述：**

快捷指令栏 (`/help`, `/new-bot`, `/my-bots`) 使用默认 Ant Design 小按钮，与周围背景融合，可发现性差。

**修复方案：**

```css
.quickCommands {
  padding: 8px 20px;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  background: #f8fafc;
  border-top: 1px solid #e5e9f2;
}
```

将 `<Button size="small">` 替换为语义化样式：

```tsx
<button
  key={command}
  className="quickCommandChip"
  onClick={() => onSubmit(command)}
  disabled={loading}
>
  {command}
</button>
```

```css
.quickCommandChip {
  background: #e6f0ff;
  color: #1668dc;
  border: 1px solid #c2d9ff;
  border-radius: 20px;
  padding: 3px 12px;
  font-size: 12px;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.15s;
}
.quickCommandChip:hover:not(:disabled) { background: #d0e5ff; }
.quickCommandChip:disabled { opacity: 0.5; cursor: not-allowed; }
```

---

### P2-3：字体和 CSS 变量系统

**问题描述：**

当前无字体声明，色值以魔法数字散落在 CSS 中（如 `#172033`、`#7b8798` 各出现多次），难以维护。

**修复方案：**

`apps/web/index.html` 的 `<head>` 中添加：

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

`styles.css` 顶部添加 `:root` 变量：

```css
:root {
  /* 品牌色 */
  --color-primary:       #1668dc;
  --color-primary-light: #e6f0ff;
  --color-primary-muted: #c2d9ff;

  /* 中性/背景 */
  --color-bg-app:     #f0f3f8;
  --color-bg-surface: #ffffff;
  --color-bg-sidebar: #111c2d;
  --color-border:     #e2e8f0;
  --color-border-subtle: rgba(255,255,255,0.10);

  /* 文字 */
  --color-text-primary:   #172033;
  --color-text-secondary: #64748b;
  --color-text-disabled:  #94a3b8;

  /* 状态 */
  --color-online:  #22c55e;
  --color-offline: #94a3b8;

  /* 间距 */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 48px;

  /* 圆角 */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
}

body {
  margin: 0;
  background: var(--color-bg-app);
  color: var(--color-text-primary);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 14px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}
```

---

## 数据流影响

本次修改均为**纯 UI/样式层**改动，不涉及：
- API 接口变更
- 状态管理（Zustand store）变更
- 数据类型变更

唯一需要注意的是 `ConversationChat` Header 中移除了显示 `conversation.target_id`（一个内部 ID 字符串），改为显示在线状态文字。如有调试需求可保留为 `title` 属性。

---

## 错误处理

无新增错误路径，修改不影响现有的 `ApiError` 处理逻辑。

---

## 测试策略

| 测试项 | 验证方式 |
|--------|---------|
| 布局响应式 | 在 720px、860px、1024px、1440px 宽度下截图对比 |
| 气泡方向感 | 发送/接收消息，确认圆角方向正确 |
| 登录页深色主题 | Ant Design 表单在深色背景下的对比度（WCAG AA ≥ 4.5:1） |
| 导航 Tooltip | 悬浮每个图标，确认 Tooltip 正确显示文字 |
| 快捷指令可用性 | 点击 `/help` 等指令确认正常发送 |

---

## 实施顺序建议

1. **CSS 变量** (`styles.css` `:root`) — 无破坏性，可独立合并
2. **字体** (`index.html`) — 无破坏性，可独立合并
3. **布局 + 导航图标栏** — 需要同步改 CSS 和 TSX，建议一个 PR
4. **气泡样式** — 独立 PR，仅改 CSS
5. **登录页深色** — 注意 Ant Design ConfigProvider 范围，建议独立 PR
6. **联系人图标色彩 + 快捷指令** — 独立 PR

---

## 回滚说明

所有改动限于 `styles.css` 和 `App.tsx` 两个文件，无数据库迁移或 API 变更，回滚只需 `git revert` 对应 commit 即可。
