# Chat Workspace UI Optimization Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve the OpenIM chat workspace information architecture, conversation scanning, business-facing headers, and mobile list-to-chat layout for Issue #24.

**Architecture:** Keep the implementation frontend-only and scoped to the existing React/Vite web app. Add small display helpers and focused components where they reduce `App.tsx` complexity, then use CSS state classes to support desktop three-column layout and mobile list/detail surfaces.

**Tech Stack:** React, TypeScript, TanStack Query, Ant Design, lucide-react, Vite, CSS.

---

## Approved Inputs

- Issue: https://github.com/Jason-Bai/openim/issues/24
- PRD: `docs/product/requirements/REQ-0024-chat-workspace-ui.md`
- UX design: `docs/product/designs/REQ-0024-chat-workspace-ui.md`
- Technical design: `docs/engineering/designs/REQ-0024-chat-workspace-ui.md`
- Registry: `docs/workflow/active/REQ-0024-chat-workspace-ui.yml`

## Scope

Use one implementation Issue and one feature branch:

- Issue: `#24 Chat workspace information architecture and responsive UI optimization`
- Branch: `feature/24-chat-workspace-ui`
- Worktree: `/Users/baiyu/.config/superpowers/worktrees/openim/feature-24-chat-workspace-ui`

Do not split backend and frontend. This requirement is frontend-only and independently shippable as one UI slice.

## Pre-Development Gate

After this plan is approved:

- Sync local `main` to `origin/main`.
- Create `feature/24-chat-workspace-ui` from updated `main`.
- Create the dedicated worktree.
- Update the registry with the branch and worktree.
- Move registry phase to `development` only after the worktree exists.

## File Structure

- Create `apps/web/src/utils/conversationDisplay.ts`
  - Owns deterministic preview cleanup, conversation status text, and technical metadata label helpers.
  - Keep helpers pure and independent from React.
- Create `apps/web/src/components/ConversationHeader.tsx`
  - Owns chat/profile header display, mobile back button, status subtitle, and technical detail affordance.
- Create `apps/web/src/components/ConversationListItem.tsx`
  - Owns list row structure for sessions, including title, status indicator, and plain-text preview.
- Modify `apps/web/src/pages/App.tsx`
  - Add mobile surface state.
  - Wire list/detail transitions.
  - Replace inline session rows and chat header with focused components.
  - Keep data fetching and mutations in place.
- Modify `apps/web/src/components/AppSidebar.tsx`
  - Improve compact mobile top-bar behavior and account/logout presentation.
- Modify `apps/web/src/styles.css`
  - Add desktop refinements and mobile list/detail state classes.
  - Reduce mobile rich-message gutters and keep composer reachable.
- Create `docs/tests/REQ-0024-chat-workspace-ui-test-report.md`
  - Record command and browser QA evidence after implementation.
- Modify `docs/workflow/active/REQ-0024-chat-workspace-ui.yml`
  - Update phase, branch/worktree, PR links, test report, and review states as gates progress.

## Chunk 1: Display Helpers And Session List

### Task 1: Add Conversation Display Helpers

**Files:**
- Create: `apps/web/src/utils/conversationDisplay.ts`
- Modify: `apps/web/src/pages/App.tsx`

- [ ] **Step 1: Create pure display helper module**

Add helpers:

```ts
import type { Conversation } from "../api/openim";

const MAX_PREVIEW_LENGTH = 80;

export function formatConversationPreview(value?: string | null) {
  const plain = markdownToPlainText(value || "");
  if (!plain) return "暂无消息";
  return plain.length > MAX_PREVIEW_LENGTH ? `${plain.slice(0, MAX_PREVIEW_LENGTH)}...` : plain;
}

export function conversationStatusText(conversation: Conversation) {
  if (conversation.target_type === "system_default_bot") return "System assistant · Online";
  if (conversation.target_type === "openclaw_bot") {
    return conversation.online ? "OpenClaw assistant · Connected" : "OpenClaw assistant · Disconnected";
  }
  return conversation.online ? "Direct message · Online" : "Direct message · Offline";
}

export function conversationTechnicalDetail(conversation: Conversation) {
  if (conversation.target_type === "openclaw_bot") return `BOT_ID: ${conversation.target_id}`;
  if (conversation.target_type === "system_default_bot") return `Target: ${conversation.target_id}`;
  return `User ID: ${conversation.target_id}`;
}

function markdownToPlainText(value: string) {
  return value
    .replace(/```[\s\S]*?```/g, "代码片段")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/^\s*[-*]\s+\[[ xX]\]\s+/gm, "")
    .replace(/^\s*[-*]\s+/gm, "")
    .replace(/^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/gm, " ")
    .replace(/[>*_`~]/g, "")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/\s+/g, " ")
    .trim();
}
```

- [ ] **Step 2: Replace raw session preview usage**

In `SessionsList`, replace:

```tsx
subtitle={item.last_message || item.target_id}
```

with:

```tsx
subtitle={formatConversationPreview(item.last_message)}
```

- [ ] **Step 3: Run TypeScript check**

Run:

```bash
npm run test -w apps/web
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add apps/web/src/utils/conversationDisplay.ts apps/web/src/pages/App.tsx
git commit -m "feat: clean conversation previews"
```

## Chunk 2: Header And Metadata Hierarchy

### Task 2: Extract Conversation Header

**Files:**
- Create: `apps/web/src/components/ConversationHeader.tsx`
- Modify: `apps/web/src/pages/App.tsx`
- Modify: `apps/web/src/styles.css`

- [ ] **Step 1: Create `ConversationHeader`**

Implement a small header component that accepts:

```ts
type ConversationHeaderProps = {
  conversation: Conversation;
  showBack?: boolean;
  onBack?: () => void;
};
```

Render:

- Optional icon-only back button with `aria-label="返回会话列表"`.
- Conversation title.
- `conversationStatusText(conversation)` as the primary subtitle.
- A secondary small detail/copy affordance for `conversationTechnicalDetail(conversation)`.

Use Ant Design `Button` and `Tooltip` or `Popover`. Keep BOT ID out of the main subtitle.

- [ ] **Step 2: Wire `ConversationChat` to use the header**

Replace the inline `<header className="chatHeader">` in `ConversationChat` with:

```tsx
<ConversationHeader conversation={conversation} showBack={showBack} onBack={onBack} />
```

Add props to `ConversationChat`:

```ts
showBack?: boolean;
onBack?: () => void;
```

- [ ] **Step 3: Add focused header styles**

Add styles for:

- `.chatHeader`
- `.chatHeaderMain`
- `.chatHeaderTitle`
- `.chatHeaderSubtitle`
- `.chatHeaderActions`
- `.chatMobileBackButton`

Ensure the header does not wrap awkwardly on mobile.

- [ ] **Step 4: Run TypeScript check**

Run:

```bash
npm run test -w apps/web
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/components/ConversationHeader.tsx apps/web/src/pages/App.tsx apps/web/src/styles.css
git commit -m "feat: add business-facing conversation header"
```

## Chunk 3: Mobile List-To-Detail Layout

### Task 3: Add Mobile Surface State

**Files:**
- Modify: `apps/web/src/pages/App.tsx`
- Modify: `apps/web/src/styles.css`

- [ ] **Step 1: Add mobile surface state**

In `ChatPage`, add:

```ts
const [mobileSurface, setMobileSurface] = useState<"list" | "detail">("list");
```

When selecting a conversation or profile, set detail:

```ts
setSelected({ type: "conversation", conversationId });
setMobileSurface("detail");
```

When changing menu, return to list:

```ts
setMenu(nextMenu);
setMobileSurface("list");
```

When opening a conversation from guide/profile mutation success, set detail.

- [ ] **Step 2: Add shell state classes**

Set root class:

```tsx
<main className={`shell ${mobileSurface === "detail" ? "mobileDetail" : "mobileList"}`}>
```

Pass `showBack={mobileSurface === "detail"}` and `onBack={() => setMobileSurface("list")}` to conversation/profile detail surfaces where needed.

- [ ] **Step 3: Update mobile CSS**

At `max-width: 860px`:

- `.shell` should use one column and stable full-height rows.
- `.mobileList .chat` should be hidden.
- `.mobileDetail .contacts` should be hidden.
- `.mobileDetail .chat` should be visible and use full remaining height.
- `.contacts` should not be capped at `240px` in the list state if it is the primary surface.
- `.commandBar` should stay at the bottom of the chat layout.

- [ ] **Step 4: Run TypeScript check**

Run:

```bash
npm run test -w apps/web
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/pages/App.tsx apps/web/src/styles.css
git commit -m "feat: add mobile list detail chat layout"
```

## Chunk 4: Navigation, Empty States, And Rich Message Polish

### Task 4: Polish Navigation And Empty States

**Files:**
- Modify: `apps/web/src/components/AppSidebar.tsx`
- Modify: `apps/web/src/pages/App.tsx`
- Modify: `apps/web/src/styles.css`

- [ ] **Step 1: Compact mobile account controls**

Update `AppSidebar` so mobile can show a compact account area. Keep desktop behavior readable. Acceptable minimal approach:

- Truncate username.
- Keep logout button compact.
- Ensure nav buttons do not force username into multiple awkward lines.

- [ ] **Step 2: Improve guide copy**

Update `GuidePanel` copy to describe state and next action:

- Sessions: `选择一个会话继续，或通过默认 BOT 创建 OpenClaw 助手连接。`
- Contacts: `选择联系人或 AI，查看资料并开始聊天。`

Keep admin-console links out of scope.

- [ ] **Step 3: Refine mobile rich message spacing**

CSS refinements:

- Reduce `.messageList` padding on mobile.
- Set mobile `.bubble` max-width to full available width.
- Keep tables/code horizontally scrollable.
- Keep `.scrollToBottomButton` away from the composer.

- [ ] **Step 4: Run TypeScript check and build**

Run:

```bash
npm run test -w apps/web
npm run build -w apps/web
```

Expected: PASS. Vite large chunk warning is acceptable if unchanged.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/components/AppSidebar.tsx apps/web/src/pages/App.tsx apps/web/src/styles.css
git commit -m "feat: polish chat workspace navigation states"
```

## Chunk 5: Browser QA, Docs, And Registry

### Task 5: Verify UI And Record Evidence

**Files:**
- Create: `docs/tests/REQ-0024-chat-workspace-ui-test-report.md`
- Modify: `docs/workflow/active/REQ-0024-chat-workspace-ui.yml`

- [ ] **Step 1: Run command verification**

Run:

```bash
npm run test -w apps/web
npm run build -w apps/web
```

Expected: PASS.

- [ ] **Step 2: Run browser QA**

Start the web app and test:

- Desktop `1280x720`.
- Desktop `1440x900`.
- Mobile `390x844`.

Verify:

- Desktop has stable three-area layout.
- Mobile list state hides chat content.
- Mobile detail state hides list as primary content and has a back button.
- Conversation previews do not show raw Markdown syntax.
- Header subtitle shows user-facing status.
- Long rich messages remain collapsible and do not overflow horizontally.
- Composer remains reachable.

- [ ] **Step 3: Write test report**

Create `docs/tests/REQ-0024-chat-workspace-ui-test-report.md` with:

- Commands run.
- Browser viewport evidence.
- Known warnings.
- Residual risks.

- [ ] **Step 4: Update registry**

Update:

- `phase: code_review` after implementation verification.
- `docs.test_report`.
- `reviews.code_review: pending`.
- Add PR link after PR is opened.

- [ ] **Step 5: Commit**

```bash
git add docs/tests/REQ-0024-chat-workspace-ui-test-report.md docs/workflow/active/REQ-0024-chat-workspace-ui.yml
git commit -m "docs: record chat workspace ui verification"
```

## Final Verification Before PR

Run:

```bash
npm run test -w apps/web
npm run build -w apps/web
```

Expected:

- TypeScript check passes.
- Vite production build passes.
- Existing large chunk warning may remain.

Open PR:

```text
feature/24-chat-workspace-ui -> develop
```

PR body must link:

- Issue #24.
- Registry.
- PRD.
- UX design.
- Technical design.
- Implementation plan.
- Test report.
