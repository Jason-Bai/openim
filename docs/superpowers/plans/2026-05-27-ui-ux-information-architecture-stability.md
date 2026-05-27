# UI/UX Information Architecture and Stability Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make OpenIM Contacts clearer, keep chat context stable across refreshes, and add the minimum UI states/accessibility/responsive fixes required by the approved UI/UX spec.

**Architecture:** Keep the current React page structure, but move pure UI state helpers out of `App.tsx` so the already large page file does not absorb unrelated responsibilities. Use TanStack Query invalidation for server-state refresh, per-user localStorage for selected conversation restore, and existing Ant Design components for state blocks and controls. Verification uses frontend type/build checks plus Chrome UI QA; no new frontend test framework is introduced in this plan.

**Tech Stack:** React 18, TypeScript, Vite, TanStack Query, Zustand, Ant Design, lucide-react, FastAPI backend, Chrome browser QA.

---

## Source Spec

- `docs/superpowers/specs/2026-05-27-ui-ux-information-architecture-stability-design.md`

## Execution Rule

Do not implement Chunks 1-3 directly on `main`. Execute Chunk 0 first to create registry, GitHub Issues, and one branch/worktree per Issue from an up-to-date `main`.

## File Map

Workflow:

- Create `docs/workflow/active/REQ-ui-ux-information-architecture-stability.yml`: tracks the approved requirement, branch/worktree, Issues, PRs, QA, and release status.

Frontend helpers:

- Create `apps/web/src/pages/contactGroups.ts`: pure contact identity, de-duplication, and `AI 助手` / `员工联系人` grouping.
- Create `apps/web/src/pages/botCommands.ts`: pure default-BOT command classification for commands that should refresh BOT/contact state.
- Create `apps/web/src/pages/conversationSelection.ts`: pure localStorage helpers for selected conversation persistence.
- Create `apps/web/src/components/StateBlock.tsx`: small reusable state block for loading/error/empty surfaces.

Frontend app:

- Modify `apps/web/src/pages/App.tsx`: wire helpers into existing query/mutation flow, restore selected conversation once after load, pass query state to panels, and fix accessible names.
- Modify `apps/web/src/components/CopyableCodeBlock.tsx`: add accessible name to the icon-only copy button.
- Modify `apps/web/src/styles.css`: state block styling, logout target size, compact layout hardening.
- Modify `apps/web/src/api/openim.ts` only if existing types are insufficient. Expected: no API change.

Verification docs:

- Create `docs/tests/YYYY-MM-DD-ui-ux-information-architecture-stability-test-report.md`: final QA report.
- Create `docs/tests/assets/YYYY-MM-DD-uiux-*.png`: Chrome QA evidence screenshots.

Verification commands:

- `npm run test -w apps/web`
- `npm run build -w apps/web`
- `cd apps/server && uv run pytest -q` only if backend files change.

---

## Chunk 0: Workflow Setup Before Implementation

### Task 0: Create registry, Issues, and implementation worktree

**Files:**

- Create: `docs/workflow/active/REQ-ui-ux-information-architecture-stability.yml`
- Verify: `git status --short --branch`

- [ ] **Step 1: Sync local main before branching**

Run:

```bash
git checkout main
git fetch origin --prune
git pull --ff-only origin main
git status --short --branch
```

Expected: local `main` is up to date with `origin/main`, clean except known unrelated untracked files, and ready for branch/worktree creation.

- [ ] **Step 2: Create requirement registry**

Copy `docs/workflow/template.yml` to:

```text
docs/workflow/active/REQ-ui-ux-information-architecture-stability.yml
```

Fill at minimum:

```yaml
id: REQ-ui-ux-information-architecture-stability
title: UI/UX information architecture and stability
type: feature
status: active
phase: planned

docs:
  prd: docs/superpowers/specs/2026-05-27-ui-ux-information-architecture-stability-design.md
  ux: docs/superpowers/specs/2026-05-27-ui-ux-information-architecture-stability-design.md
  technical_design: docs/superpowers/specs/2026-05-27-ui-ux-information-architecture-stability-design.md
  implementation_plan: docs/superpowers/plans/2026-05-27-ui-ux-information-architecture-stability.md
  test_report: null
  release_note: null

reviews:
  product_review: approved
  ux_review: approved
  technical_review: approved
```

Expected: registry points to the approved spec and this plan.

- [ ] **Step 3: Commit registry**

Run:

```bash
git add docs/workflow/active/REQ-ui-ux-information-architecture-stability.yml
git commit -m "docs: track ui ux stability workflow"
```

Expected: workflow tracking exists before implementation work starts.

- [ ] **Step 4: Create GitHub Issues after plan approval**

Create one Issue per independently testable function:

1. Contacts grouping and de-duplication.
2. Default BOT command refresh.
3. Selected conversation restore.
4. Loading/error/empty states.
5. Accessibility and interaction target fixes.
6. Compact layout QA and fixes.

Expected: each Issue links to the spec and plan.

- [ ] **Step 5: Update registry with Issue links**

Fill `github.issues` and `execution_items` in the registry.

Expected: each Issue is traceable from the registry before code work starts.

- [ ] **Step 6: Create one implementation branch/worktree per Issue**

From up-to-date `main`, create a dedicated branch/worktree for each Issue. First set shell variables to the actual issue numbers created in Step 4. The numbers below are examples and must be replaced with the real Issue numbers before running:

```bash
CONTACTS_ISSUE=123
BOT_REFRESH_ISSUE=124
SELECTION_ISSUE=125
QUERY_STATES_ISSUE=126
ACCESSIBILITY_ISSUE=127
COMPACT_LAYOUT_ISSUE=128

git worktree add ../openim-${CONTACTS_ISSUE}-contacts-ia -b feature/${CONTACTS_ISSUE}-contacts-ia main
git worktree add ../openim-${BOT_REFRESH_ISSUE}-bot-command-refresh -b feature/${BOT_REFRESH_ISSUE}-bot-command-refresh main
git worktree add ../openim-${SELECTION_ISSUE}-selected-conversation-restore -b feature/${SELECTION_ISSUE}-selected-conversation-restore main
git worktree add ../openim-${QUERY_STATES_ISSUE}-query-states -b feature/${QUERY_STATES_ISSUE}-query-states main
git worktree add ../openim-${ACCESSIBILITY_ISSUE}-accessibility-targets -b feature/${ACCESSIBILITY_ISSUE}-accessibility-targets main
git worktree add ../openim-${COMPACT_LAYOUT_ISSUE}-compact-layout -b feature/${COMPACT_LAYOUT_ISSUE}-compact-layout main
```

Expected: each Issue has an isolated branch/worktree and implementation does not continue on `main`.

- [ ] **Step 7: Update registry execution items with branch/worktree**

For each Issue, add an `execution_items` entry. This example shows the contacts Issue; repeat with the real Issue URL, branch, and worktree for every execution item:

```yaml
phase: development
execution_items:
  - issue: https://github.com/Jason-Bai/openim/issues/123
    branch: feature/123-contacts-ia
    worktree: /Users/baiyu/workspaces/gitlab/openim-123-contacts-ia
    phase: development
    status: active
```

Also keep top-level `github.issue`, `branch.name`, and `branch.worktree` pointed at the first active execution item for compatibility with the registry schema.

Expected: registry reflects all active worktrees before Chunks 1-3 begin.

---

## Chunk 1: Contacts IA, BOT Command Refresh, and Conversation Restore

Run each task in the worktree for its matching GitHub Issue:

- Task 1 and Task 2: Contacts grouping and de-duplication Issue.
- Task 3: Default BOT command refresh Issue.
- Task 4: Selected conversation restore Issue.

### Task 1: Add focused contact grouping helper

**Files:**

- Create: `apps/web/src/pages/contactGroups.ts`
- Verify: `npm run test -w apps/web`

- [ ] **Step 1: Inspect current contact and conversation types**

Run:

```bash
sed -n '1,180p' apps/web/src/api/openim.ts
sed -n '1,220p' apps/web/src/pages/App.tsx
```

Expected: `ContactItem`, `Conversation`, and `User` types already provide the fields needed by the helpers.

- [ ] **Step 2: Create contact grouping helper**

Create `apps/web/src/pages/contactGroups.ts`:

```ts
import type { ContactItem } from "../api/openim";

export type ContactGroups = {
  ai: ContactItem[];
  employees: ContactItem[];
};

export function contactIdentity(item: ContactItem) {
  if (item.contact_type === "system_default_bot") return "system_default_bot:default_bot";
  if (item.contact_type === "openclaw_bot") return `openclaw_bot:${item.bot.bot_id}`;
  return `user:${item.user.id}`;
}

function mergeContactByIdentity(current: ContactItem | undefined, next: ContactItem) {
  if (!current) return next;
  if (current.contact_type !== next.contact_type) return next;
  return contactPayloadScore(next) >= contactPayloadScore(current) ? next : current;
}

function contactPayloadScore(item: ContactItem) {
  if (item.contact_type === "system_default_bot") {
    return [item.id, item.title, item.subtitle, item.online].filter(Boolean).length;
  }
  if (item.contact_type === "openclaw_bot") {
    return [
      item.bot.name,
      item.bot.bot_id,
      item.bot.connect_status,
      item.bot.binding_status,
      item.bot.last_seen_at,
      item.bot.first_connected_at
    ].filter(Boolean).length;
  }
  return [
    item.user.id,
    item.user.username,
    item.user.employee_id,
    item.user.real_name,
    item.user.relationship,
    item.user.last_seen_at
  ].filter(Boolean).length;
}

export function groupedContacts(data?: { ai: ContactItem[]; all: ContactItem[] }): ContactGroups {
  const merged = new Map<string, ContactItem>();
  for (const item of [...(data?.ai ?? []), ...(data?.all ?? [])]) {
    const key = contactIdentity(item);
    merged.set(key, mergeContactByIdentity(merged.get(key), item));
  }
  const ai: ContactItem[] = [];
  const employees: ContactItem[] = [];
  for (const item of merged.values()) {
    if (item.contact_type === "user") employees.push(item);
    else ai.push(item);
  }
  return { ai, employees };
}
```

Expected: identity matches the spec: default BOT by fixed identity, OpenClaw BOT by `bot_id`, employee by `user.id`. When duplicate identities differ, the richer payload wins by field-presence score.

- [ ] **Step 3: Run type check**

Run:

```bash
npm run test -w apps/web
```

Expected: pass.

- [ ] **Step 4: Commit helper file**

Run:

```bash
git add apps/web/src/pages/contactGroups.ts
git commit -m "feat: add contact grouping helper"
```

Expected: one focused contact helper commit in the contacts Issue worktree.

### Task 2: Wire Contacts panel to `AI 助手` / `员工联系人`

**Files:**

- Modify: `apps/web/src/pages/App.tsx`
- Verify: `npm run test -w apps/web`

- [ ] **Step 1: Import contact grouping helper**

In `App.tsx`, add:

```ts
import { groupedContacts } from "./contactGroups";
```

Expected: no helper implementation is added directly to `App.tsx`.

- [ ] **Step 2: Derive grouped contacts in `ChatPage`**

Add:

```ts
const contactGroups = useMemo(() => groupedContacts(contactsQuery.data), [contactsQuery.data]);
```

Expected: Contacts grouping is derived from the existing query result.

- [ ] **Step 3: Pass grouped contacts into `ContactsPanel`**

Change the `ContactsPanel` call:

```tsx
<ContactsPanel
  ai={contactGroups.ai}
  employees={contactGroups.employees}
  selected={selectedView}
  onSelect={(target) => setSelected({ type: "profile", target })}
/>
```

Update `ContactsPanel` props from `all` to `employees`.

Expected: the render path no longer displays `contactsQuery.data?.all` directly.

- [ ] **Step 4: Update Contacts section labels**

In `ContactsPanel`, render:

```tsx
<Typography.Text type="secondary">AI 助手</Typography.Text>
...
<Typography.Text type="secondary">员工联系人</Typography.Text>
```

Expected: `已添加的 AI` and `全部联系人` no longer appear in the UI.

- [ ] **Step 5: Resolve selected profiles from grouped contacts**

Change selected view derivation:

```ts
const selectedView = useMemo(
  () => resolveSelectedView(selected, [...contactGroups.ai, ...contactGroups.employees]),
  [contactGroups.ai, contactGroups.employees, selected]
);
```

Update helper signature:

```ts
function resolveSelectedView(selected: SelectedView, contacts: ContactItem[]): SelectedView
```

Expected: selected profile details still update after contact query refresh.

- [ ] **Step 6: Run type check**

Run:

```bash
npm run test -w apps/web
```

Expected: pass.

- [ ] **Step 7: Commit task**

Run:

```bash
git add apps/web/src/pages/App.tsx
git commit -m "feat: group contacts by object type"
```

Expected: one focused commit.

### Task 3: Refresh contacts and conversations after default BOT state commands

**Files:**

- Create: `apps/web/src/pages/botCommands.ts`
- Modify: `apps/web/src/pages/App.tsx`
- Verify: `npm run test -w apps/web`

- [ ] **Step 1: Create default BOT command helper**

Create `apps/web/src/pages/botCommands.ts` in the BOT command refresh Issue worktree:

```ts
const BOT_STATE_COMMANDS = new Set(["/new-bot", "/delete-bot", "/connect", "/disconnect", "/diagnose"]);

export function affectsBotState(content: string) {
  const command = content.trim().split(/\s+/, 1)[0] ?? "";
  return BOT_STATE_COMMANDS.has(command);
}
```

Expected: helper is local to the BOT command refresh branch and covers only approved command prefixes.

- [ ] **Step 2: Import command helper**

In `App.tsx`, add:

```ts
import { affectsBotState } from "./botCommands";
```

Expected: command parsing stays outside `App.tsx`.

- [ ] **Step 3: Include submit-time conversation context in mutation variables**

Update `sendMutation` variable type to include:

```ts
conversationTargetType: string;
```

Change `submitMessage` mutation call:

```ts
sendMutation.mutate({
  conversationId: activeConversation.id,
  conversationTargetType: activeConversation.target_type,
  content,
  tempId
});
```

Expected: refresh decisions use the conversation that submitted the message, not a potentially stale `activeConversation` at mutation resolution time.

- [ ] **Step 4: Invalidate after successful relevant default BOT command**

In `sendMutation.onSuccess`, after message/conversation cache updates:

```ts
if (vars.conversationTargetType === "system_default_bot" && affectsBotState(vars.content)) {
  queryClient.invalidateQueries({ queryKey: ["contacts"] });
  queryClient.invalidateQueries({ queryKey: ["conversations"] });
}
```

Expected: `/new-bot`, `/delete-bot`, `/connect`, `/disconnect`, and `/diagnose` refresh contacts/conversations after successful send response even if the user switches conversations before the response arrives.

This intentionally uses the spec-approved broad invalidation fallback because current command responses do not provide reliable structured command-level success metadata.

- [ ] **Step 5: Confirm failures do not refresh false state**

Read `sendMutation.onError`.

Expected: no contacts/conversations optimistic update is added on error.

- [ ] **Step 6: Run type check**

Run:

```bash
npm run test -w apps/web
```

Expected: pass.

- [ ] **Step 7: Commit task**

Run:

```bash
git add apps/web/src/pages/botCommands.ts apps/web/src/pages/App.tsx
git commit -m "feat: refresh bot state after default bot commands"
```

Expected: one focused commit.

### Task 4: Persist and restore selected conversation per user

**Files:**

- Create: `apps/web/src/pages/conversationSelection.ts`
- Modify: `apps/web/src/pages/App.tsx`
- Verify: `npm run test -w apps/web`

- [ ] **Step 1: Create selected conversation storage helper**

Create `apps/web/src/pages/conversationSelection.ts` in the selected conversation restore Issue worktree:

```ts
export function selectedConversationKey(userId: number) {
  return `openim_selected_conversation_${userId}`;
}

export function readSelectedConversation(userId: number) {
  try {
    return window.localStorage.getItem(selectedConversationKey(userId));
  } catch {
    return null;
  }
}

export function writeSelectedConversation(userId: number, conversationId: string) {
  try {
    window.localStorage.setItem(selectedConversationKey(userId), conversationId);
  } catch {
    // Selection restore is a convenience; storage failures should not block chat.
  }
}

export function clearSelectedConversation(userId: number) {
  try {
    window.localStorage.removeItem(selectedConversationKey(userId));
  } catch {
    // Selection restore is a convenience; storage failures should not block logout.
  }
}
```

Expected: helper is local to the selected conversation restore branch and localStorage failures are non-fatal.

- [ ] **Step 2: Import selection helpers and `useRef`**

Update imports:

```ts
import { useEffect, useMemo, useRef, useState } from "react";
import {
  clearSelectedConversation,
  readSelectedConversation,
  writeSelectedConversation
} from "./conversationSelection";
```

Expected: localStorage implementation remains outside `App.tsx`.

- [ ] **Step 3: Pass full user into `ChatPage`**

Change `App`:

```tsx
return <ChatPage token={token} user={user} onLogout={clearAuth} />;
```

Change `ChatPage` props:

```ts
function ChatPage({ token, user, onLogout }: { token: string; user: User; onLogout: () => void }) {
```

Use `user.username` where `username` was used.

Expected: `ChatPage` has `user.id` for per-user storage.

- [ ] **Step 4: Add selection helper inside `ChatPage`**

Add:

```ts
const selectConversation = (conversationId: string) => {
  writeSelectedConversation(user.id, conversationId);
  setSelected({ type: "conversation", conversationId });
};
```

Use it in:

- `SessionsList onSelect`.
- `ensureMutation.onSuccess`.

Expected: manual and programmatic conversation selection are persisted.

- [ ] **Step 5: Restore selection once after conversations first load**

Add:

```ts
const hasRestoredSelection = useRef(false);
```

Add effect:

```ts
useEffect(() => {
  const conversations = conversationsQuery.data?.items;
  if (!conversations || hasRestoredSelection.current) return;
  hasRestoredSelection.current = true;

  setSelected((current) => {
    if (current.type !== "guide") return current;
    const stored = readSelectedConversation(user.id);
    const restored = stored ? conversations.find((item) => item.id === stored) : undefined;
    const fallback = conversations[0];
    const next = restored ?? fallback;
    if (next) {
      writeSelectedConversation(user.id, next.id);
      return { type: "conversation", conversationId: next.id };
    }
    return current;
  });
}, [conversationsQuery.data?.items, user.id]);
```

Expected: restore happens only once after initial load and does not repeatedly override the user after they switch to Contacts/profile/guide.

- [ ] **Step 6: Handle selected conversation that disappears**

Add a separate effect:

```ts
useEffect(() => {
  const conversations = conversationsQuery.data?.items;
  if (!conversations || selected.type !== "conversation") return;
  if (conversations.some((item) => item.id === selected.conversationId)) return;
  const fallback = conversations[0];
  if (fallback) {
    writeSelectedConversation(user.id, fallback.id);
    setSelected({ type: "conversation", conversationId: fallback.id });
  } else {
    clearSelectedConversation(user.id);
    setSelected({ type: "guide" });
  }
}, [conversationsQuery.data?.items, selected, user.id]);
```

Expected: a stale selected conversation falls back to the first API conversation, or guide if no conversations exist.

- [ ] **Step 7: Clear selected conversation on logout**

Wrap logout:

```tsx
onClick={() => {
  clearSelectedConversation(user.id);
  onLogout();
}}
```

Expected: logout clears the current user's selected conversation.

- [ ] **Step 8: Add manual verification notes before commit**

Before committing, manually reason through:

```text
valid stored id -> restored once
stale stored id -> first API conversation selected and persisted
no conversations -> guide
explicit user switch after load -> not overridden by later refetch
logout -> storage key cleared
```

Expected: implementation matches each case.

- [ ] **Step 9: Run type check**

Run:

```bash
npm run test -w apps/web
```

Expected: pass.

- [ ] **Step 10: Commit task**

Run:

```bash
git add apps/web/src/pages/conversationSelection.ts apps/web/src/pages/App.tsx
git commit -m "feat: restore selected conversation"
```

Expected: one focused commit.

---

## Chunk 2: Loading/Error/Empty States, Accessibility, and Responsive Basics

Run each task in the worktree for its matching GitHub Issue:

- Task 5: Loading/error/empty states Issue.
- Task 6: Accessibility and interaction target fixes Issue.
- Task 7: Compact layout QA and fixes Issue.

### Task 5: Add list-level loading, error, and empty states

**Files:**

- Create: `apps/web/src/components/StateBlock.tsx`
- Modify: `apps/web/src/pages/App.tsx`
- Modify: `apps/web/src/styles.css`
- Verify: `npm run test -w apps/web`

- [ ] **Step 1: Create reusable state block component**

Create `apps/web/src/components/StateBlock.tsx`:

```tsx
import { Button, Typography } from "antd";

export function StateBlock({
  title,
  actionLabel,
  actionDisabled,
  onAction
}: {
  title: string;
  actionLabel?: string;
  actionDisabled?: boolean;
  onAction?: () => void;
}) {
  return (
    <div className="stateBlock">
      <Typography.Text type="secondary">{title}</Typography.Text>
      {actionLabel && (
        <Button size="small" onClick={onAction} disabled={actionDisabled}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
```

Expected: pending actions can render a disabled `打开中...` button.

- [ ] **Step 2: Extend `SessionsList` props**

Update `SessionsList` props:

```ts
loading: boolean;
error: boolean;
onRetry: () => void;
onOpenDefaultBot: () => void;
openingDefaultBot: boolean;
```

Render before normal list:

```tsx
if (loading) return <StateBlock title="加载会话中..." />;
if (error) return <StateBlock title="会话加载失败" actionLabel="重试" onAction={onRetry} />;
if (!items.length) {
  return (
    <StateBlock
      title="暂无会话"
      actionLabel={openingDefaultBot ? "打开中..." : "打开默认 BOT"}
      actionDisabled={openingDefaultBot}
      onAction={openingDefaultBot ? undefined : onOpenDefaultBot}
    />
  );
}
```

Expected: loading, error, and empty are distinct.

- [ ] **Step 3: Pass conversation query state from `ChatPage`**

Update `SessionsList` call:

```tsx
<SessionsList
  items={conversationsQuery.data?.items ?? []}
  loading={conversationsQuery.isLoading}
  error={conversationsQuery.isError}
  onRetry={() => conversationsQuery.refetch()}
  onOpenDefaultBot={() => ensureMutation.mutate({ type: "system_default_bot", id: "default_bot" })}
  openingDefaultBot={ensureMutation.isPending}
  selected={selectedView}
  onSelect={selectConversation}
/>
```

Expected: query state is rendered instead of false empty state.

- [ ] **Step 4: Extend `ContactsPanel` for loading/error/empty**

Add props:

```ts
loading: boolean;
error: boolean;
onRetry: () => void;
```

Render:

```tsx
if (loading) return <StateBlock title="加载联系人中..." />;
if (error) return <StateBlock title="联系人加载失败" actionLabel="重试" onAction={onRetry} />;
```

Inside the panel:

```tsx
{!ai.length && <StateBlock title="AI 助手加载异常" actionLabel="重试" onAction={onRetry} />}
{!employees.length && <StateBlock title="暂无员工联系人" />}
```

Expected: contacts loading/error/empty are explicit.

- [ ] **Step 5: Add message loading/error/empty states**

In `ConversationChat`, add props:

```ts
messagesLoading: boolean;
messagesError: boolean;
onRetryMessages: () => void;
```

Inside `.messageList`, before mapping messages:

```tsx
{messagesLoading && <StateBlock title="加载消息中..." />}
{messagesError && <StateBlock title="消息加载失败" actionLabel="重试" onAction={onRetryMessages} />}
{!messagesLoading && !messagesError && !messages.length && <StateBlock title="暂无消息，发送第一条消息" />}
```

Pass from `ChatPage`:

```tsx
messagesLoading={messagesQuery.isLoading}
messagesError={messagesQuery.isError}
onRetryMessages={() => messagesQuery.refetch()}
```

Expected: selected conversations no longer show a blank message area while loading/error/empty.

- [ ] **Step 6: Add state block CSS**

In `styles.css`, add:

```css
.stateBlock {
  color: #7b8798;
  font-size: 13px;
  line-height: 1.5;
  padding: 12px;
  border: 1px dashed #d9e0ea;
  border-radius: 8px;
  background: #fafcff;
  display: grid;
  gap: 8px;
}

.stateBlock .ant-btn {
  width: fit-content;
}
```

Remove `.emptyList` if no usage remains.

Expected: no dead `.emptyList` usage remains unless intentionally retained.

- [ ] **Step 7: Run type check**

Run:

```bash
npm run test -w apps/web
```

Expected: pass.

- [ ] **Step 8: Commit task**

Run:

```bash
git add apps/web/src/components/StateBlock.tsx apps/web/src/pages/App.tsx apps/web/src/styles.css
git commit -m "feat: add explicit app loading states"
```

Expected: one focused commit.

### Task 6: Fix accessibility names and interaction target sizes

**Files:**

- Modify: `apps/web/src/pages/App.tsx`
- Modify: `apps/web/src/components/CopyableCodeBlock.tsx`
- Modify: `apps/web/src/styles.css`
- Verify: `npm run test -w apps/web`

- [ ] **Step 1: Add explicit login button aria labels**

In `LoginPage`, update submit button:

```tsx
<Button type="primary" htmlType="submit" block aria-label={mode === "login" ? "登录" : "注册并登录"}>
  {mode === "login" ? "登录" : "注册并登录"}
</Button>
```

Expected: browser role/name lookup can target `登录`.

- [ ] **Step 2: Confirm send button aria label exists**

Check current send button:

```tsx
<Button aria-label="发送消息" ... />
```

Expected: no change needed unless implementation removed it.

- [ ] **Step 3: Add copy button aria label**

In `apps/web/src/components/CopyableCodeBlock.tsx`, update the icon-only copy button:

```tsx
<Button
  aria-label="复制代码"
  className="copyButton"
  size="small"
  icon={<Copy size={14} />}
  onClick={async () => {
    await navigator.clipboard.writeText(content);
    message.success("已复制");
  }}
/>
```

Expected: every known icon-only button in the current workflow has an accessible name.

- [ ] **Step 4: Increase logout button target height**

In `styles.css`, ensure:

```css
.accountFooter .ant-btn {
  justify-content: center;
  min-height: 32px;
}
```

Expected: `退出` button height is at least 32px.

- [ ] **Step 5: Run type check**

Run:

```bash
npm run test -w apps/web
```

Expected: pass.

- [ ] **Step 6: Commit task**

Run:

```bash
git add apps/web/src/pages/App.tsx apps/web/src/components/CopyableCodeBlock.tsx apps/web/src/styles.css
git commit -m "fix: improve core control accessibility"
```

Expected: one focused commit.

### Task 7: Harden <= 860px responsive behavior

**Files:**

- Modify: `apps/web/src/styles.css`
- Verify: `npm run test -w apps/web`, focused browser layout check

- [ ] **Step 1: Inspect current media query**

Run:

```bash
sed -n '240,380p' apps/web/src/styles.css
```

Expected: existing `@media (max-width: 860px)` stacks shell into `mainMenu`, `contacts`, `chat`.

- [ ] **Step 2: Ensure mobile shell can fit chat input**

In the media query, update:

```css
.shell {
  min-height: 100vh;
  height: 100dvh;
  grid-template-columns: 1fr;
  grid-template-rows: auto minmax(120px, 32vh) minmax(0, 1fr);
}

.chat {
  min-height: 0;
}
```

Expected: contacts list cannot consume the full viewport and hide chat input.

- [ ] **Step 3: Prevent top nav/account overflow**

In the media query, add:

```css
.mainMenu {
  overflow-x: auto;
}

.brand {
  flex: 0 0 auto;
}

.accountFooter {
  min-width: 0;
}
```

Expected: long usernames do not force page-level horizontal overflow.

- [ ] **Step 4: Bound message and input content unconditionally**

Add:

```css
.bubble,
.codeBlock {
  max-width: min(100%, 720px);
  overflow-wrap: anywhere;
}

.commandBar {
  padding: 12px;
}
```

Expected: message bubbles, long BOT IDs/tokens, code blocks, and input bar stay inside the viewport.

- [ ] **Step 5: Run type check**

Run:

```bash
npm run test -w apps/web
```

Expected: pass.

- [ ] **Step 6: Run focused compact layout browser check**

With dev servers running, use Chrome or the in-app browser at a viewport <= 860px. Evaluate:

```js
({
  viewport: { width: window.innerWidth, height: window.innerHeight },
  horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth,
  commandBarVisible: Boolean(document.querySelector(".commandBar")?.getBoundingClientRect().height)
})
```

Expected: `horizontalOverflow` is `false`. When a conversation is selected, `commandBarVisible` is `true`.

- [ ] **Step 7: Commit task**

Run:

```bash
git add apps/web/src/styles.css
git commit -m "fix: harden compact layout"
```

Expected: one focused commit.

---

## Chunk 3: Verification and QA Evidence

### Task 8: Run full frontend verification

**Files:**

- No source files expected unless verification reveals a defect.
- Verify: frontend type/build.

- [ ] **Step 1: Run frontend type check**

Run:

```bash
npm run test -w apps/web
```

Expected: pass.

- [ ] **Step 2: Run frontend build**

Run:

```bash
npm run build -w apps/web
```

Expected: pass and Vite build completes.

- [ ] **Step 3: Run backend tests only if backend changed**

If any backend files changed, run:

```bash
cd apps/server && uv run pytest -q
```

Expected: pass.

- [ ] **Step 4: Fix and rerun failed verification before committing**

If a verification command fails:

1. Fix the source issue.
2. Rerun the failed command.
3. If the fix could affect another verification command, rerun that command too.

Expected: all previously failed commands pass before committing fixes.

- [ ] **Step 5: Commit verification fixes only after rerun passes**

Run only if fixes were needed:

```bash
git add <changed-files>
git commit -m "fix: address ui ux verification issues"
```

Expected: no uncommitted source fixes remain.

### Task 9: Run Chrome UI QA

**Files:**

- Create: `docs/tests/YYYY-MM-DD-ui-ux-information-architecture-stability-test-report.md`
- Create: `docs/tests/assets/YYYY-MM-DD-uiux-*.png`

- [ ] **Step 1: Start backend**

Run:

```bash
cd apps/server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Expected: backend listens on `http://127.0.0.1:8080`.

- [ ] **Step 2: Start frontend**

In another terminal:

```bash
npm run dev -w apps/web -- --host 0.0.0.0
```

Expected: frontend listens on `http://localhost:5173/`.

- [ ] **Step 3: Execute desktop Chrome flow**

Using Chrome plugin:

1. Register a fresh user.
2. Open default BOT.
3. Send `/help`.
4. Send `/new-bot`; capture the new `bot_id`.
5. Switch to Contacts.
6. Verify `AI 助手` and `员工联系人` labels.
7. Verify default BOT appears once.
8. Verify new OpenClaw BOT appears once without page refresh.
9. Open default BOT profile.
10. Open OpenClaw BOT profile.
11. Open self profile.
12. Open another employee profile if fixture data exists.
13. Select a conversation, refresh, and verify selected conversation restore.
14. Verify login submit button role/name `登录`.
15. Verify logout button height is at least 32px.

Expected: all pass; capture screenshots for the report.

- [ ] **Step 4: Execute command refresh QA**

Using the BOT created in Step 3:

1. Send `/diagnose {bot_id}` and verify Contacts/Conversations refresh without duplicate or false state.
2. Send `/connect {bot_id}` and verify the UI remains consistent after refresh.
3. Send `/disconnect {bot_id}` and verify the UI remains consistent after refresh.
4. Send an invalid command such as `/connect missing_bot_id` and verify no false BOT/contact state is created.
5. If using a disposable test BOT, send `/delete-bot {bot_id}` and verify it disappears from `AI 助手`.

Expected: all scoped command refresh behavior is covered. If `/delete-bot` is skipped, document why in residual risk.

- [ ] **Step 5: Execute compact viewport QA**

Use Chrome or the in-app browser at <= 860px.

Check:

1. Login/register visible and usable.
2. Main menu does not cause page-level horizontal overflow.
3. Contact/session list scrolls without hiding the chat input.
4. Default BOT can be opened.
5. `/help` can be sent.
6. Contact profile can be opened.

Expected: core path works with no critical overlap.

- [ ] **Step 6: Verify error states with a temporary mock API server**

Use a temporary local mock API server that is not committed. Start frontend with `VITE_API_BASE_URL` pointing at the mock server. The mock should return successful auth/me data as needed, and controlled API errors for:

```text
GET /api/conversations
GET /api/contacts
GET /api/conversations/{id}/messages
```

Expected UI states:

1. Conversations error renders `会话加载失败` and retry.
2. Contacts error renders `联系人加载失败` and retry.
3. Messages error renders `消息加载失败` and retry.

Do not commit mock server code unless it is intentionally added as a supported test utility in a separate reviewed change.

- [ ] **Step 7: Write QA report**

Create `docs/tests/YYYY-MM-DD-ui-ux-information-architecture-stability-test-report.md` with:

```md
# UI/UX Information Architecture and Stability Test Report

Date:
Environment:
Commit:

## Commands
- npm run test -w apps/web: PASS/FAIL
- npm run build -w apps/web: PASS/FAIL

## Chrome QA Results
| Case | Result | Evidence |
| --- | --- | --- |

## Command Refresh Results
| Command | Result | Notes |
| --- | --- | --- |

## Error State Results
| Surface | Result | Method |
| --- | --- | --- |

## Issues Found
- None, or list severity and repro steps.

## Residual Risk
- Note skipped `/delete-bot`, viewport limitations, or mock API limitations.
```

Expected: report links to screenshots under `docs/tests/assets/`.

- [ ] **Step 8: Commit QA evidence**

Run:

```bash
git add docs/tests/YYYY-MM-DD-ui-ux-information-architecture-stability-test-report.md docs/tests/assets/YYYY-MM-DD-uiux-*.png
git commit -m "test: document ui ux stability qa"
```

Expected: QA evidence is captured separately from source changes.
