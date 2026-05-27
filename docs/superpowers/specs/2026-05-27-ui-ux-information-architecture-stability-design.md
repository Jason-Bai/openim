# OpenIM UI/UX Information Architecture and Stability Design

Date: 2026-05-27
Status: Draft approved for spec review

## 1. Background

Chrome-based UI/UX QA found that OpenIM's core IM flows are functional, but several interaction details make the product feel less stable than the backend behavior actually is:

- Contacts repeat the same BOTs across `已添加的 AI` and `全部联系人`.
- A BOT created through `/new-bot` is not visible in Contacts until another mutation triggers a contacts refresh.
- Page refresh keeps login state and backend-backed conversations, but resets the selected conversation to the guide panel.
- Contacts, conversations, and messages do not clearly distinguish loading, empty, and error states.
- Some controls have weak accessibility or small interaction targets.

This spec turns the QA report into one product requirement. Implementation may still be split into independent GitHub Issues by minimum user-visible function.

Source QA report:

- `docs/tests/2026-05-27-ui-ux-qa-optimization-report.md`

## 2. Goals

This work should make the basic OpenIM chat experience clearer and more stable:

1. Reorganize Contacts by object type so AI assistants and employee contacts are easy to distinguish.
2. Remove duplicate contact entries for the same BOT or employee.
3. Refresh contacts and conversations after default BOT commands that can change BOT state.
4. Restore or choose a reasonable active conversation after page refresh.
5. Add explicit loading, empty, and error states for server-backed lists and message history.
6. Improve basic accessibility and interaction target quality.
7. Keep the core flow usable at widths below or equal to 860px without a full mobile redesign.

## 3. Non-Goals

This requirement does not include:

- Full mobile IM redesign.
- Contact search, favorites, departments, or organization tree.
- A new right-side profile/status panel.
- Full visual redesign of chat bubbles or the main shell.
- A workflow/process change for page tester roles. QA role organization should be handled later as workflow documentation.
- Backend command metadata changes. The first implementation can use query invalidation after successful command responses.

## 4. Users

- Employee user: registers, logs in, talks to default BOT, creates OpenClaw assistant slots, opens contacts, and sends messages.
- Product/QA reviewer: verifies that the UI states are understandable and the core workflow is testable.
- Developer: maintains the frontend state boundaries and automated testability.

## 5. User Stories

### P0

1. As an employee, I want Contacts to clearly separate AI assistants from employee contacts, so I do not see the same BOT in multiple groups.
2. As an employee, after I send `/new-bot`, I want the new OpenClaw assistant to appear in `AI 助手` without refreshing the page.
3. As an employee, after refreshing the page, I want to return to the conversation I was using, or at least the most recent conversation.
4. As an employee, I want loading, empty, and error states to be explicit, so I know whether the app is still loading, has no data, or failed.

### P1

5. As an employee on a narrow screen, I want login, contacts, opening a conversation, and sending a message to remain usable.
6. As a tester, I want important controls to have stable accessible names and reasonable target sizes, so manual and automated testing are reliable.

### P2

7. As an employee, I want empty states to tell me what to do next instead of only saying that nothing exists.

## 6. Product Design

### 6.1 Contacts Information Architecture

Replace the current Contacts groups:

```text
已添加的 AI
全部联系人
```

with:

```text
AI 助手
员工联系人
```

Rules:

- `AI 助手` contains:
  - The system default BOT.
  - OpenClaw employee-assistant BOTs visible to the current employee.
- `员工联系人` contains:
  - The current employee.
  - Other employee accounts.
- The same logical object must appear only once in Contacts.
- Clicking any object opens the existing profile panel.
- Offline or unbound OpenClaw BOTs keep the disabled `发送消息` action and a clear explanation.

De-duplication identity:

- System default BOT: `contact_type=system_default_bot` and `id=default_bot`.
- OpenClaw BOT: `contact_type=openclaw_bot` and `bot.bot_id`.
- Employee user: `contact_type=user` and `user.id`.

If the backend returns the same identity from both existing `ai` and `all` contact arrays, render one entry in the target group above. Prefer the richer object payload when fields differ.

This spec intentionally removes the `全部联系人` concept for now. The current product does not yet have search, favorites, organization grouping, or contact filters, so a full directory group adds ambiguity without enough benefit.

### 6.2 Default BOT Command Refresh

After the user sends a default BOT command that can change BOT state, the frontend should refresh related server state after a successful command response.

Commands in scope:

```text
/new-bot
/delete-bot {bot_id}
/connect {bot_id}
/disconnect {bot_id}
/diagnose {bot_id}
```

Minimum behavior:

- Invalidate/refetch `contacts` after successful command response.
- Invalidate/refetch `conversations` after successful command response.
- Keep the current messages update behavior from the send response; do not add a second messages fetch unless needed for correctness.
- If the command fails, do not optimistically change contacts or conversations.

Successful command response means:

- The message-send mutation succeeds.
- The returned default BOT reply is not an error/failure reply for the command.

If command-level success cannot be reliably detected from the current response shape, the initial implementation may invalidate `contacts` and `conversations` after any successful default BOT command send that matches the in-scope command prefix. This is acceptable because invalidation is conservative and does not fabricate UI state.

Future-compatible behavior:

- If backend command responses later include structured metadata, replace broad invalidation with metadata-driven cache updates.

### 6.3 Conversation Selection Restore

Store the selected conversation per logged-in user.

Suggested storage key:

```text
openim_selected_conversation_{user.id}
```

Restore rules:

1. When conversations load, if the stored conversation ID still exists, select it.
2. If the stored conversation ID does not exist and there are conversations, select the first conversation from the current `GET /conversations` response. That API is treated as the source of truth for recency ordering; if the API order changes later, restore behavior follows the API.
3. If there are no conversations, show the guide panel.
4. When the user manually selects a conversation, update the stored ID.
5. On logout, clear the selected conversation for the current user.

The restore behavior should not override an explicit user selection made after the page has loaded.

### 6.4 Loading, Empty, and Error States

Server-backed UI surfaces must show separate states.

Conversations:

- Loading: `加载会话中...` or list skeleton.
- Error: `会话加载失败` with a retry action.
- Empty: `暂无会话` plus an action to open the default BOT.

Contacts:

- Loading: `加载联系人中...` or list skeleton.
- Error: `联系人加载失败` with a retry action.
- Empty:
  - `AI 助手`: default BOT should normally exist; if missing, show a retry-oriented abnormal empty state.
  - `员工联系人`: `暂无员工联系人`.

Messages:

- Loading: `加载消息中...`.
- Error: `消息加载失败` with a retry action.
- Empty: `暂无消息，发送第一条消息`.

### 6.5 Accessibility and Interaction Targets

Requirements:

- Login submit button accessible name should be `登录`.
- Icon-only buttons must have `aria-label`.
- `退出` button height must be at least 32px.
- Primary actions should be locatable by stable role/name in browser tests.

### 6.6 Basic Responsive Behavior

At widths <= 860px:

- No page-level horizontal overflow.
- Main menu remains a top horizontal area.
- Contact/session list can scroll without hiding the chat input.
- Chat input remains visible and usable.
- Text does not overflow buttons, list items, or message bubbles.
- Core path remains usable:
  - Register or login.
  - Open default BOT.
  - Send `/help`.
  - Switch to Contacts.
  - Open a contact profile.

This is a basic usability requirement, not a full mobile navigation redesign.

## 7. Technical Design

### 7.1 Frontend Boundaries

Likely touched areas:

- `apps/web/src/pages/App.tsx`
- `apps/web/src/styles.css`
- Existing API/client/state files only if needed for clean state boundaries.

Recommended frontend units:

- Contacts grouping: derive grouped contact arrays from `contactsQuery.data`.
- Conversation selection persistence: isolate storage read/write helpers near current selected state logic or in a small local helper.
- Query state rendering: keep list-level loading/error/empty handling close to `SessionsList`, `ContactsPanel`, and `ConversationChat`.
- Command refresh: update the message-send success path to invalidate `contacts` and `conversations` when the active conversation is the system default BOT and the sent content is a relevant command.

### 7.2 Data Flow

Contacts:

```text
GET /contacts
  -> ai/all data from backend
  -> frontend derives:
       AI 助手
       员工联系人
  -> render unique entries
```

Default BOT command:

```text
send message to default BOT
  -> backend returns updated conversation/messages
  -> merge messages and upsert conversation
  -> if command may affect BOT state:
       invalidate contacts
       invalidate conversations
```

Conversation restore:

```text
auth user available
  -> conversations loaded
  -> stored selected conversation valid?
       yes: select stored conversation
       no: select most recent conversation if present
       none: guide
```

### 7.3 Error Handling

- Query errors should render retryable UI instead of looking empty.
- Command failures should keep current error toast behavior and avoid cache refresh unless the mutation succeeded.
- Invalid stored conversation IDs should be ignored and overwritten when a new valid conversation is selected.
- Local storage read errors should not block the app; fall back to guide or most recent conversation.

## 8. Acceptance Criteria

### Contacts

- Contacts shows only `AI 助手` and `员工联系人`.
- Default BOT appears exactly once.
- Each OpenClaw BOT appears exactly once.
- Employee accounts appear only in `员工联系人`.
- Clicking default BOT, OpenClaw BOT, self, and another employee opens the correct profile.

### BOT Command Refresh

- After `/new-bot`, the new BOT appears in `AI 助手` without page refresh.
- After `/connect` or `/disconnect`, contact/conversation online state refreshes after the command response.
- After `/delete-bot`, the deleted BOT no longer appears in `AI 助手` after the command response.
- After `/diagnose`, contacts/conversations are refreshed after the command response without changing state incorrectly.
- Failed commands do not create false contact or conversation state.

### Conversation Restore

- Refreshing with a valid selected conversation restores that conversation.
- If the stored conversation no longer exists, the first conversation from `GET /conversations` is selected.
- If no conversations exist, the guide panel is shown.
- Logging out clears the current user's selected conversation state.

### States

- Conversations, contacts, and messages each have loading, empty, and error states.
- Error states provide a retry action.
- Empty states include next-step copy or an action where appropriate.

### Accessibility and Interaction

- Login submit button has accessible name `登录`.
- `退出` button height is at least 32px.
- Icon-only send button has an accessible name.
- Main actions are stable under browser role/name testing.

### Responsive

- At <= 860px, there is no page-level horizontal overflow.
- Login, open default BOT, send `/help`, switch Contacts, and open a profile are usable.
- Chat input remains visible when a conversation is selected.

## 9. Testing Plan

Commands:

```bash
npm run test -w apps/web
npm run build -w apps/web
```

Run backend tests only if backend API behavior changes:

```bash
cd apps/server && uv run pytest -q
```

Chrome UI test:

1. Register a new user and enter the main shell.
2. Open default BOT.
3. Send `/help`.
4. Send `/new-bot`; verify the new BOT appears under `AI 助手` without refreshing.
5. Verify Contacts has no duplicate default BOT or OpenClaw BOT.
6. Send `/diagnose {bot_id}`; verify contacts/conversations refresh without duplicate or false state.
7. If a removable test BOT is available, send `/delete-bot {bot_id}`; verify it disappears from `AI 助手`.
8. Select a conversation, refresh, and verify selection restore.
9. Verify query error states by temporarily forcing API failures in a controlled test build or browser session:
   - conversations: make `GET /api/conversations` return or simulate an error and verify retry UI.
   - contacts: make `GET /api/contacts` return or simulate an error and verify retry UI.
   - messages: make `GET /api/conversations/{id}/messages` return or simulate an error and verify retry UI.
   The implementation plan should choose the least invasive method, such as MSW/component tests if introduced, dependency-injected API mocks, or a temporary browser-test-only network interception. Do not commit production code that hardcodes forced failures.
10. Check <= 860px core path.
11. Save screenshots under `docs/tests/assets/` and write a test report under `docs/tests/`.

## 10. Suggested GitHub Issue Split

Use one PRD and split execution by independently testable function:

1. Contacts grouping: `AI 助手` / `员工联系人` and de-duplication.
2. Default BOT command refresh for contacts/conversations.
3. Selected conversation restore after refresh.
4. Loading/error/empty states for conversations, contacts, and messages.
5. Accessibility and interaction target fixes.
6. Basic <= 860px responsive QA and fixes.

Suggested priority:

- P0: Issues 1, 2, 3.
- P1: Issues 4, 5, 6.

## 11. Open Questions

No blocking open questions. The following can be decided during implementation planning:

- Whether loading states use simple text or Ant Design skeletons.
- Whether command refresh detection starts as string matching or a small command parser helper.
