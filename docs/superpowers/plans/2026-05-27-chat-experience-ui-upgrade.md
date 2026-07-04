# Chat Experience UI Upgrade Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade OpenIM's chat experience with an enterprise IM sidebar, safe rich message rendering with top-positioned folding, and non-interrupting scroll-to-bottom behavior.

**Architecture:** Keep backend contracts unchanged and implement this as focused frontend slices. Extract presentational and behavior components out of `App.tsx` while keeping data fetching and mutation ownership in `ChatPage`. Use sanitizer-backed Markdown rendering and isolated scroll-state hooks.

**Tech Stack:** React 18, TypeScript, Vite, Ant Design, TanStack Query, lucide-react, react-markdown, remark-gfm, rehype-raw, rehype-sanitize.

## Pre-Implementation Gate

- [ ] Confirm this plan with the user.
- [ ] Create GitHub Issues after plan approval only:
  - Sidebar redesign.
  - Message renderer with Markdown, safe HTML, and long-content folding.
  - Scroll-to-bottom affordance.
- [ ] Sync `main` before creating any development worktree:

```bash
git fetch origin --prune
git checkout main
git pull --ff-only origin main
```

- [ ] Create one branch/worktree per approved Issue.
- [ ] Update `docs/workflow/active/REQ-chat-experience-ui-upgrade.yml` with Issue URLs, branch names, and worktree paths before development.

---

## File Structure

Expected frontend files:

```text
apps/web/src/components/AppSidebar.tsx
apps/web/src/components/MessageRenderer.tsx
apps/web/src/components/MessageContent.tsx
apps/web/src/components/CollapsibleMessage.tsx
apps/web/src/components/ScrollToBottomButton.tsx
apps/web/src/components/useConversationScroll.ts
apps/web/src/pages/App.tsx
apps/web/src/styles.css
apps/web/package.json
package-lock.json
```

Expected documentation / QA files:

```text
docs/tests/REQ-chat-experience-ui-upgrade-test-report.md
docs/tests/assets/REQ-chat-experience-ui-upgrade-*.png
docs/workflow/active/REQ-chat-experience-ui-upgrade.yml
```

---

## Chunk 1: Sidebar Redesign

### Task 1: Extract `AppSidebar`

**Files:**

- Create: `apps/web/src/components/AppSidebar.tsx`
- Modify: `apps/web/src/pages/App.tsx`
- Modify: `apps/web/src/styles.css`

- [ ] **Step 1: Create presentational sidebar component**

Create `apps/web/src/components/AppSidebar.tsx`:

```tsx
import { Button } from "antd";
import { LogOut, MessageCircle, UsersRound } from "lucide-react";

type MenuKey = "sessions" | "contacts";

export function AppSidebar({
  menu,
  username,
  onMenuChange,
  onLogout
}: {
  menu: MenuKey;
  username: string;
  onMenuChange: (menu: MenuKey) => void;
  onLogout: () => void;
}) {
  return (
    <aside className="appSidebar" aria-label="OpenIM 主导航">
      <div className="sidebarBrand">OpenIM</div>
      <nav className="sidebarNav" aria-label="主导航">
        <button
          type="button"
          className={`sidebarNavItem ${menu === "sessions" ? "active" : ""}`}
          aria-current={menu === "sessions" ? "page" : undefined}
          onClick={() => onMenuChange("sessions")}
        >
          <MessageCircle size={18} />
          <span>会话</span>
        </button>
        <button
          type="button"
          className={`sidebarNavItem ${menu === "contacts" ? "active" : ""}`}
          aria-current={menu === "contacts" ? "page" : undefined}
          onClick={() => onMenuChange("contacts")}
        >
          <UsersRound size={18} />
          <span>通讯录</span>
        </button>
      </nav>
      <div className="sidebarSpacer" />
      <div className="sidebarAccount">
        <div className="sidebarAccountName" title={username}>
          {username}
        </div>
        <Button size="small" icon={<LogOut size={14} />} onClick={onLogout}>
          退出
        </Button>
      </div>
    </aside>
  );
}
```

- [ ] **Step 2: Wire `AppSidebar` into `ChatPage`**

Modify `apps/web/src/pages/App.tsx`:

- Import `AppSidebar`.
- Remove inline `<aside className="mainMenu">...</aside>`.
- Replace it with:

```tsx
<AppSidebar
  menu={menu}
  username={username}
  onLogout={onLogout}
  onMenuChange={(nextMenu) => {
    setMenu(nextMenu);
    setSelected((current) =>
      nextMenu === "sessions" && current.type === "conversation" ? current : { type: "guide" }
    );
  }}
/>
```

- [ ] **Step 3: Remove unused imports**

Remove unused `LogOut`, `UsersRound`, or duplicate sidebar icons from `App.tsx`.

- [ ] **Step 4: Update sidebar CSS**

Modify `apps/web/src/styles.css`:

```css
.appSidebar {
  background: #fbfdff;
  border-right: 1px solid #e1e7ef;
  color: #172033;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.sidebarBrand {
  min-height: 40px;
  display: flex;
  align-items: center;
  padding: 0 10px;
  font-size: 18px;
  font-weight: 700;
  color: #111827;
}

.sidebarNav {
  display: grid;
  gap: 6px;
}

.sidebarNavItem {
  width: 100%;
  min-height: 40px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: #526173;
  display: grid;
  grid-template-columns: 20px 1fr;
  align-items: center;
  gap: 8px;
  padding: 0 10px;
  font: inherit;
  font-weight: 600;
  text-align: left;
  cursor: pointer;
}

.sidebarNavItem:hover {
  background: #f1f5fa;
  color: #172033;
}

.sidebarNavItem.active {
  background: #e8f1ff;
  color: #1668dc;
}

.sidebarSpacer {
  flex: 1;
}

.sidebarAccount {
  border-top: 1px solid #e1e7ef;
  padding-top: 12px;
  display: grid;
  gap: 8px;
}

.sidebarAccountName {
  color: #344154;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.35;
  overflow-wrap: anywhere;
}
```

Update mobile media query by replacing `.mainMenu`, `.menuSpacer`, `.accountFooter` selectors with `.appSidebar`, `.sidebarSpacer`, `.sidebarAccount`.

- [ ] **Step 5: Run type/build check**

Run:

```bash
npm run build -w apps/web
```

Expected: PASS.

- [ ] **Step 6: Browser QA**

Run the app and verify:

- Desktop sidebar is light enterprise IM style.
- Active nav item is obvious.
- Account name does not overflow.
- <= 860px does not introduce horizontal overflow.

- [ ] **Step 7: Commit sidebar slice**

```bash
git add apps/web/src/components/AppSidebar.tsx apps/web/src/pages/App.tsx apps/web/src/styles.css
git commit -m "feat: redesign chat sidebar"
```

---

## Chunk 2: Message Renderer And Long-Content Folding

### Task 2: Add rich rendering dependencies

**Files:**

- Modify: `apps/web/package.json`
- Modify: `package-lock.json`

- [ ] **Step 1: Install dependencies**

Run:

```bash
npm install -w apps/web react-markdown remark-gfm rehype-raw rehype-sanitize
```

Expected:

- `apps/web/package.json` includes the four dependencies.
- `package-lock.json` updates.

- [ ] **Step 2: Build check after install**

Run:

```bash
npm run build -w apps/web
```

Expected: PASS or only fail because components are not implemented yet if the install altered type resolution unexpectedly.

### Task 3: Create message rendering components

**Files:**

- Create: `apps/web/src/components/MessageContent.tsx`
- Create: `apps/web/src/components/CollapsibleMessage.tsx`
- Create: `apps/web/src/components/MessageRenderer.tsx`
- Modify: `apps/web/src/pages/App.tsx`
- Modify: `apps/web/src/styles.css`

- [ ] **Step 1: Create `MessageContent`**

Create `apps/web/src/components/MessageContent.tsx`:

```tsx
import ReactMarkdown from "react-markdown";
import rehypeRaw from "rehype-raw";
import rehypeSanitize, { defaultSchema } from "rehype-sanitize";
import remarkGfm from "remark-gfm";

const safeSchema = {
  ...defaultSchema,
  tagNames: [
    ...(defaultSchema.tagNames ?? []),
    "u",
    "s",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td"
  ],
  attributes: {
    ...defaultSchema.attributes,
    a: ["href", "title"],
    th: ["align"],
    td: ["align"]
  }
};

export function MessageContent({ content }: { content: string }) {
  return (
    <div className="messageContent">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw, [rehypeSanitize, safeSchema]]}
        components={{
          a: ({ children, href, title }) => (
            <a href={href} title={title} target="_blank" rel="noreferrer noopener">
              {children}
            </a>
          )
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
```

- [ ] **Step 2: Create `CollapsibleMessage`**

Create `apps/web/src/components/CollapsibleMessage.tsx`:

```tsx
import type { ReactNode } from "react";
import { useLayoutEffect, useRef, useState } from "react";

export function CollapsibleMessage({
  collapsedHeight = 360,
  children
}: {
  collapsedHeight?: number;
  children: ReactNode;
}) {
  const contentRef = useRef<HTMLDivElement>(null);
  const [expanded, setExpanded] = useState(false);
  const [collapsible, setCollapsible] = useState(false);

  useLayoutEffect(function measureCollapsibleContent() {
    const element = contentRef.current;
    if (!element) return;

    function update() {
      setCollapsible(element.scrollHeight > collapsedHeight + 8);
    }

    update();
    if (typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(update);
    observer.observe(element);
    return function disconnectObserver() {
      observer.disconnect();
    };
  }, [collapsedHeight, children]);

  return (
    <div className="collapsibleMessage">
      {collapsible ? (
        <button
          type="button"
          className="messageExpandButton"
          onClick={() => setExpanded((current) => !current)}
        >
          {expanded ? "收起" : "展开全文"}
        </button>
      ) : null}
      <div
        ref={contentRef}
        className={`messageFoldBody ${collapsible && !expanded ? "collapsed" : ""}`}
        style={collapsible && !expanded ? { maxHeight: collapsedHeight } : undefined}
      >
        {children}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Create `MessageRenderer`**

Create `apps/web/src/components/MessageRenderer.tsx`:

```tsx
import type { ConversationMessage } from "../api/openim";
import { CopyableCodeBlock } from "./CopyableCodeBlock";
import { CollapsibleMessage } from "./CollapsibleMessage";
import { MessageContent } from "./MessageContent";

export function MessageRenderer({ message }: { message: ConversationMessage }) {
  if (message.content_type === "code") {
    return <CopyableCodeBlock content={message.content} />;
  }

  if (message.sender_type === "user") {
    return <div className="bubble plainBubble">{message.content}</div>;
  }

  return (
    <div className="bubble richBubble">
      <CollapsibleMessage>
        <MessageContent content={message.content} />
      </CollapsibleMessage>
    </div>
  );
}
```

- [ ] **Step 4: Use `MessageRenderer` in `ConversationChat`**

Modify `apps/web/src/pages/App.tsx`:

- Import `MessageRenderer`.
- Replace inline message render branch:

```tsx
{item.content_type === "code" ? (
  <CopyableCodeBlock content={item.content} />
) : (
  <div className="bubble">{item.content}</div>
)}
```

with:

```tsx
<MessageRenderer message={item} />
```

- Remove `CopyableCodeBlock` import from `App.tsx` if no longer used.

- [ ] **Step 5: Add renderer CSS**

Modify `apps/web/src/styles.css`:

```css
.plainBubble {
  white-space: pre-wrap;
}

.richBubble {
  white-space: normal;
}

.messageContent {
  overflow-wrap: anywhere;
}

.messageContent > :first-child {
  margin-top: 0;
}

.messageContent > :last-child {
  margin-bottom: 0;
}

.messageContent p,
.messageContent ul,
.messageContent ol,
.messageContent blockquote,
.messageContent table,
.messageContent pre {
  margin: 0 0 10px;
}

.messageContent pre {
  max-width: 100%;
  overflow: auto;
  background: #101827;
  color: #e6edf7;
  border-radius: 8px;
  padding: 12px;
}

.messageContent code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.messageContent :not(pre) > code {
  background: #eef2f7;
  border-radius: 4px;
  padding: 1px 4px;
}

.messageContent table {
  display: block;
  max-width: 100%;
  overflow-x: auto;
  border-collapse: collapse;
}

.messageContent th,
.messageContent td {
  border: 1px solid #d8e0ea;
  padding: 6px 8px;
}

.messageContent blockquote {
  border-left: 3px solid #b7c4d6;
  color: #526173;
  padding-left: 10px;
}

.collapsibleMessage {
  display: grid;
  gap: 8px;
}

.messageExpandButton {
  width: fit-content;
  border: 0;
  background: transparent;
  color: #1668dc;
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  padding: 0;
}

.messageFoldBody.collapsed {
  overflow: hidden;
}
```

- [ ] **Step 6: Run build**

Run:

```bash
npm run build -w apps/web
```

Expected: PASS.

- [ ] **Step 7: Manual QA rich content**

Use an existing OpenClaw conversation or seed messages manually through UI/API and verify:

- Markdown heading/list/code/table renders.
- Safe HTML paragraph/list/table/link renders.
- `<script>alert(1)</script>` does not execute.
- `<img src=x onerror=alert(1)>` does not execute.
- `[bad](javascript:alert(1))` is neutralized.
- Long message shows top `展开全文`.
- Expanded state shows top `收起`.

- [ ] **Step 8: Commit message renderer slice**

```bash
git add apps/web/package.json package-lock.json apps/web/src/components/MessageContent.tsx apps/web/src/components/CollapsibleMessage.tsx apps/web/src/components/MessageRenderer.tsx apps/web/src/pages/App.tsx apps/web/src/styles.css
git commit -m "feat: render rich chat messages safely"
```

---

## Chunk 3: Scroll-To-Bottom Affordance

### Task 4: Add conversation scroll hook and button

**Files:**

- Create: `apps/web/src/components/useConversationScroll.ts`
- Create: `apps/web/src/components/ScrollToBottomButton.tsx`
- Modify: `apps/web/src/pages/App.tsx`
- Modify: `apps/web/src/styles.css`

- [ ] **Step 1: Create `useConversationScroll`**

Create `apps/web/src/components/useConversationScroll.ts`:

```ts
import { useCallback, useEffect, useRef, useState } from "react";
import type { ConversationMessage } from "../api/openim";

const NEAR_BOTTOM_PX = 80;

export function useConversationScroll({
  conversationId,
  messages
}: {
  conversationId: string;
  messages: ConversationMessage[];
}) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const nearBottomRef = useRef(true);
  const lastMessageIdRef = useRef<string | null>(null);
  const [isNearBottom, setIsNearBottom] = useState(true);
  const [hasNewMessages, setHasNewMessages] = useState(false);

  const setNearBottom = useCallback((next: boolean) => {
    nearBottomRef.current = next;
    setIsNearBottom((current) => (current === next ? current : next));
    if (next) setHasNewMessages(false);
  }, []);

  const measureNearBottom = useCallback(() => {
    const element = scrollRef.current;
    if (!element) return true;
    return element.scrollHeight - element.scrollTop - element.clientHeight <= NEAR_BOTTOM_PX;
  }, []);

  const scrollToBottom = useCallback(() => {
    const element = scrollRef.current;
    if (!element) return;
    element.scrollTo({ top: element.scrollHeight, behavior: "smooth" });
    setNearBottom(true);
  }, [setNearBottom]);

  const handleScroll = useCallback(() => {
    setNearBottom(measureNearBottom());
  }, [measureNearBottom, setNearBottom]);

  useEffect(function resetOnConversationChange() {
    lastMessageIdRef.current = null;
    setHasNewMessages(false);
    requestAnimationFrame(() => {
      const element = scrollRef.current;
      if (!element) return;
      element.scrollTop = element.scrollHeight;
      setNearBottom(true);
    });
  }, [conversationId, setNearBottom]);

  useEffect(function syncLatestMessageScroll() {
    const lastMessage = messages[messages.length - 1];
    if (!lastMessage) return;
    if (lastMessageIdRef.current === lastMessage.id) return;

    const previousId = lastMessageIdRef.current;
    lastMessageIdRef.current = lastMessage.id;

    requestAnimationFrame(() => {
      const shouldFollow =
        previousId === null || nearBottomRef.current || lastMessage.sender_type === "user";
      const element = scrollRef.current;
      if (!element) return;
      if (shouldFollow) {
        element.scrollTop = element.scrollHeight;
        setNearBottom(true);
        return;
      }
      setHasNewMessages(true);
      setNearBottom(measureNearBottom());
    });
  }, [measureNearBottom, messages, setNearBottom]);

  return {
    scrollRef,
    isNearBottom,
    hasNewMessages,
    handleScroll,
    scrollToBottom
  };
}
```

- [ ] **Step 2: Create `ScrollToBottomButton`**

Create `apps/web/src/components/ScrollToBottomButton.tsx`:

```tsx
import { Button } from "antd";
import { ArrowDown } from "lucide-react";

export function ScrollToBottomButton({
  hasNewMessages,
  onClick
}: {
  hasNewMessages: boolean;
  onClick: () => void;
}) {
  return (
    <div className="scrollToBottom">
      {hasNewMessages ? <span className="newMessageBadge">新消息</span> : null}
      <Button
        aria-label="滚动到最新消息"
        shape="circle"
        type="primary"
        icon={<ArrowDown size={18} />}
        onClick={onClick}
      />
    </div>
  );
}
```

- [ ] **Step 3: Wire hook in `ConversationChat`**

Modify `ConversationChat` in `apps/web/src/pages/App.tsx`:

- Import `useConversationScroll` and `ScrollToBottomButton`.
- Inside component:

```tsx
const { scrollRef, isNearBottom, hasNewMessages, handleScroll, scrollToBottom } =
  useConversationScroll({
    conversationId: conversation.id,
    messages
  });
```

- Change message list:

```tsx
<div className="messageList" ref={scrollRef} onScroll={handleScroll}>
  ...
</div>
{!isNearBottom ? (
  <ScrollToBottomButton hasNewMessages={hasNewMessages} onClick={scrollToBottom} />
) : null}
```

- Ensure `.chat` can position the button:

```css
.chat {
  position: relative;
}
```

- [ ] **Step 4: Add scroll button CSS**

Modify `apps/web/src/styles.css`:

```css
.scrollToBottom {
  position: absolute;
  right: 24px;
  bottom: 92px;
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 5;
}

.newMessageBadge {
  background: #fff;
  border: 1px solid #d8e0ea;
  border-radius: 999px;
  color: #1668dc;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 8px;
  box-shadow: 0 8px 22px rgba(23, 32, 51, 0.12);
}
```

- [ ] **Step 5: Run build**

Run:

```bash
npm run build -w apps/web
```

Expected: PASS.

- [ ] **Step 6: Browser QA scroll behavior**

Verify:

- Open a long conversation.
- Scroll upward: button appears.
- Click button: scrolls to bottom and button clears.
- Send while near bottom: follows latest message.
- Receive bot/system message while away from bottom: no forced scroll, `新消息` appears.

- [ ] **Step 7: Commit scroll slice**

```bash
git add apps/web/src/components/useConversationScroll.ts apps/web/src/components/ScrollToBottomButton.tsx apps/web/src/pages/App.tsx apps/web/src/styles.css
git commit -m "feat: add chat scroll-to-bottom control"
```

---

## Chunk 4: Final QA And Release Evidence

### Task 5: Run final verification

**Files:**

- Create: `docs/tests/REQ-chat-experience-ui-upgrade-test-report.md`
- Create: `docs/tests/assets/REQ-chat-experience-ui-upgrade-*.png`
- Modify: `docs/workflow/active/REQ-chat-experience-ui-upgrade.yml`

- [ ] **Step 1: Run frontend build**

Run:

```bash
npm run build -w apps/web
```

Expected: PASS.

- [ ] **Step 2: Run workspace test command**

Run:

```bash
npm test --workspaces --if-present
```

Expected: PASS.

- [ ] **Step 3: Start local app**

Run backend and frontend if not already running:

```bash
cd apps/server && uv run uvicorn app.main:app --host 0.0.0.0 --port 8080
```

```bash
npm run dev -w apps/web -- --host 0.0.0.0
```

- [ ] **Step 4: Browser QA**

Use the browser plugin to capture evidence for:

- Sidebar desktop.
- Sidebar <= 860px.
- Markdown rich message.
- Safe HTML rich message.
- Unsafe HTML neutralized.
- Long folded message with top `展开全文`.
- Expanded message with top `收起`.
- Scroll-to-bottom button with `新消息`.

- [ ] **Step 5: Write test report**

Create `docs/tests/REQ-chat-experience-ui-upgrade-test-report.md`:

```markdown
# REQ-chat-experience-ui-upgrade Test Report

Date: 2026-05-27

## Environment

- Frontend:
- Backend:
- Branch:

## Commands

- `npm run build -w apps/web`: PASS
- `npm test --workspaces --if-present`: PASS

## Browser QA

- Sidebar desktop: PASS
- Sidebar <= 860px: PASS
- Markdown rendering: PASS
- Safe HTML rendering: PASS
- Unsafe HTML neutralized: PASS
- Long message folding: PASS
- Scroll-to-bottom: PASS

## Evidence

- `docs/tests/assets/REQ-chat-experience-ui-upgrade-01-sidebar.png`
- `docs/tests/assets/REQ-chat-experience-ui-upgrade-02-rich-message.png`
- `docs/tests/assets/REQ-chat-experience-ui-upgrade-03-scroll-bottom.png`

## Risks / Notes

- ...
```

- [ ] **Step 6: Update registry QA fields**

Update `docs/workflow/active/REQ-chat-experience-ui-upgrade.yml`:

```yaml
docs:
  test_report: docs/tests/REQ-chat-experience-ui-upgrade-test-report.md
reviews:
  qa_review: approved
```

Only set `qa_review: approved` after evidence exists.

- [ ] **Step 7: Commit QA evidence**

```bash
git add docs/tests/REQ-chat-experience-ui-upgrade-test-report.md docs/tests/assets/REQ-chat-experience-ui-upgrade-* docs/workflow/active/REQ-chat-experience-ui-upgrade.yml
git commit -m "test: document chat experience ui qa"
```

---

## Execution Notes

- Do not develop on `main`.
- Do not create all three implementation slices in one branch unless the user explicitly approves combining Issues.
- The recommended order is:
  1. Sidebar redesign.
  2. Message renderer and folding.
  3. Scroll-to-bottom affordance.
- The message renderer slice is the highest risk because it adds dependencies and security-sensitive rendering.
- If implementation reveals the need for backend content metadata, stop and return to technical review before changing backend contracts.
