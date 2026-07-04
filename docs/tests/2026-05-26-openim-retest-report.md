# OpenIM Retest Report

Date: 2026-05-26
Environment: local frontend `http://127.0.0.1:5173`, local backend `http://127.0.0.1:8080`

## Scope

- Registration and login
- Conversation entry points
- Default BOT command flow
- OpenClaw BOT creation and connection info flow
- Contacts list and friend request flow
- Offline OpenClaw BOT messaging experience

## Verification Summary

| Check | Result |
| --- | --- |
| Backend tests, `cd apps/server && uv run pytest` | Pass, 14 passed |
| Web type check, `npm run test -w apps/web` | Pass |
| Plugin build, `npm run build -w packages/openclaw-bot-plugin` | Pass |
| Chrome manual retest | Pass with issues, no console errors or warnings observed |
| P0 script, `npm run e2e:p0` | Fail |

## Findings

### BUG-001: P0 automation fails because the current conversation model differs from the script expectation

Severity: P1

Steps:

1. Run `npm run e2e:p0`.
2. Observe the script after registration and login.

Actual:

- The script fails with `default bot conversation missing`.
- A direct API probe confirms that a new user can register and login successfully, but `GET /api/conversations` returns `[]`.

Expected:

- P0 validation should match the product's current supported flow.
- Either default BOT conversation should be created automatically after login, or the P0 script and README should use the current `POST /api/conversations/ensure` flow.

Notes:

- Current UI can still open the default BOT through `通讯录 -> 默认 BOT -> 发送消息`, which creates the conversation on demand.
- This appears to be an automation/documentation mismatch with the current implementation rather than total feature failure.

### BUG-002: Login error remains visible after switching to register mode

Severity: P2

Steps:

1. On the login page, enter an invalid username and password.
2. Submit the login form.
3. Switch from `登录` to `注册`.

Actual:

- The alert `用户名或密码错误` remains visible on the register form.

Expected:

- Switching auth modes should clear mode-specific errors.

Impact:

- The register form appears to be in an error state before the user has submitted registration data.

### BUG-003: Newly created offline contacts show as having left hours ago

Severity: P2

Steps:

1. Create a new user through the registration API.
2. Open the contacts list in Chrome.
3. Find the newly created user.

Actual:

- The newly created offline user is displayed as `8 小时前离开` or similar.

Expected:

- A newly created offline user should show `刚刚离开` or a neutral offline state.

Likely Cause:

- Backend time values appear to be serialized without timezone information, and the frontend parses them with `new Date(value)`, causing a local timezone offset.

### BUG-004: Friend request success does not refresh the selected profile state

Severity: P2

Steps:

1. Select a user whose relationship is `未添加`.
2. Click `添加好友`.
3. Observe the profile panel after the success toast.

Actual:

- Toast shows `好友申请已发送`.
- The selected profile still shows `关系: 未添加`.
- The `添加好友` button remains visible.

Expected:

- The selected profile should update to `等待对方确认`, and the add button should disappear or become disabled.

Screenshot:

`/Users/baiyu/workspaces/gitlab/openim/.qa-artifacts/retest-friend-profile.jpg`

### BUG-005: Offline or unbound OpenClaw BOT still allows opening a chat and sending messages

Severity: P2

Steps:

1. Create an OpenClaw BOT through the default BOT.
2. Do not connect the BOT Gateway client.
3. Open the BOT profile from contacts.
4. Click `发送消息`.
5. Send a message.

Actual:

- The profile shows `离线` and `未绑定`, but still exposes `发送消息`.
- The chat intro says `OpenClaw 员工助手已接入。你可以在这里开始对话。`
- Sending a message waits and then shows a generic failure such as `OpenClaw 员工助手暂时没有返回，请稍后重试。`

Expected:

- Sending should be disabled while the BOT is offline or unbound, or the UI should clearly instruct the user to finish connection first.

Screenshot:

`/Users/baiyu/workspaces/gitlab/openim/.qa-artifacts/retest-offline-bot-current.jpg`

## Passing Functional Checks

- Current UI default BOT command flow works after opening the default BOT through contacts.
- `/new-bot` creates a BOT and returns a `BOT_ID`.
- `/connect {bot_id}` returns connection JSON containing an `ocb_live_...` token.
- A second `/connect {bot_id}` masks the token and prompts regeneration.
- Backend tests validate Gateway auth, handshake, heartbeat, binding status, and message roundtrip behavior.
- Plugin package builds successfully.

## UI/UX Browser Walkthrough Findings

Review Method:

- Opened and interacted with the local Web UI in Chrome.
- Walked through login, form validation, first-login empty state, contacts, default BOT profile, default BOT chat, `/new-bot`, and `/connect`.
- Captured page screenshots under `/Users/baiyu/workspaces/gitlab/openim/.qa-artifacts/`.

### UX-001: First-login empty state is a dead end instead of an onboarding step

Priority: P1 UX

Observed State:

- After registration, the `会话` panel shows `暂无会话`.
- The main panel says `去通讯录选择一个联系人、AI 或群组开始。`
- There is no primary CTA, and the intended P0 next step is not visible.

Why It Matters:

- The first screen after successful registration should guide the user into the product's main job.
- Here, the user must infer that they should go to `通讯录`, choose `默认 BOT`, and then open a session.

Recommended Design:

- Replace the passive empty state with a setup action state:
  - Title: `开始接入 OpenClaw 员工助手`
  - Body: `通过默认 BOT 创建接入槽位并获取连接信息。`
  - Primary CTA: `打开默认 BOT`
  - Secondary CTA: `查看通讯录`
- If default BOT setup is the main path, route newly registered users directly into the default BOT conversation and show `/new-bot` as the suggested first action.

Screenshot:

`/Users/baiyu/workspaces/gitlab/openim/.qa-artifacts/ux-walk-empty-session.jpg`

### UX-002: Mobile layout hides navigation without replacement

Priority: P1 UX

Observed State:

- CSS at `max-width: 860px` sets `.mainMenu` and `.contacts` to `display: none`.
- The remaining `.chat` area has no visible way to switch between sessions, contacts, account actions, or logout.

Why It Matters:

- On mobile or narrow desktop windows, users can lose access to primary navigation.
- The app becomes a single-panel view without an obvious path back to contacts or sessions.

Recommended Design:

- Add mobile bottom navigation or a compact top segmented control for `会话` and `通讯录`.
- Add a mobile header with account menu and logout.
- Use a drill-in pattern: list view first, then profile/chat, with a `返回` button.

### UX-003: Default BOT command flow is visually hidden inside a generic chat input

Priority: P2 UX

Observed State:

- Default BOT input placeholder is `给 默认 BOT 发送消息`.
- The first message says `你好！输入 /help 查看可用命令。`
- There are no visible quick actions for `/help`, `/new-bot`, `/my-bots`, or `/connect`.
- After `/new-bot`, the next command is shown as plain text inside a message bubble.

Why It Matters:

- The default BOT is effectively a setup wizard, but the UI presents it as a free-form chat.
- New users may not know which commands exist or which command is recommended next.

Recommended Design:

- Add command chips above the input: `/help`, `/new-bot`, `/my-bots`.
- Change the placeholder to `输入命令，例如 /new-bot`.
- After `/new-bot`, render a structured action panel with:
  - `BOT_ID`
  - `复制 BOT_ID`
  - `获取连接信息`
  - `查看接入文档`
- Preserve typed commands for power users, but make the recommended path clickable.

Screenshot:

`/Users/baiyu/workspaces/gitlab/openim/.qa-artifacts/ux-walk-default-chat.jpg`

### UX-004: Send buttons are icon-only and have no accessible name

Priority: P2 UX

Observed State:

- Chat submit buttons render as icon-only buttons in the DOM with no accessible label.
- Browser inspection found the default BOT send button name as an empty string.

Why It Matters:

- Screen reader users do not get a meaningful button name.
- In low-context layouts, the icon-only action is less explicit than a `发送` action.

Recommended Design:

- Add `aria-label="发送消息"` to icon-only submit buttons.
- Disable the send button while input is empty.
- On wider layouts, show `发送` text next to the icon; keep icon-only on compact layouts if needed.

### UX-005: Contacts panel is hard to scan once real data accumulates

Priority: P2 UX

Observed State:

- `全部联系人` is a long flat list.
- Test, E2E, current user, stale contacts, and real contacts appear together.
- There is no search, grouping, or filtering.
- In the walkthrough data set, the contacts panel had 25 items and a scroll height of 1533px against a 929px viewport.

Why It Matters:

- The user has to scan a noisy list to find the right person or AI.
- The current user's own row and stale/test rows dilute the value of the contacts list.

Recommended Design:

- Add a sticky search field for name, username, and employee ID.
- Group by relationship: `好友`, `待确认`, `未添加`, `自己`.
- Hide or de-emphasize the current user row.
- Add filters for `全部`, `在线`, `待处理`, `AI`.
- Use compact status chips instead of long relative-time subtitles when timestamps are unreliable.

Screenshot:

`/Users/baiyu/workspaces/gitlab/openim/.qa-artifacts/ux-walk-contacts.jpg`

### UX-006: Profile panels do not clearly separate readiness from action

Priority: P2 UX

Observed State:

- User and BOT profiles show key-value rows followed by a primary button.
- Offline/unbound BOTs can still show a fully available `发送消息` primary action.
- The default BOT profile is sparse: `在线`, `系统默认助手`, and a generic `发送消息` action.

Why It Matters:

- Users read primary buttons as recommended actions.
- If an entity is offline, unbound, pending, or not ready, the UI should state that before offering action.

Recommended Design:

- Add readiness banners, for example `该 BOT 尚未连接，完成连接后才能发送消息`.
- Replace unavailable actions with setup actions such as `获取连接信息`.
- Use state-specific CTAs: `添加好友`, `等待确认`, `发消息`, `获取连接信息`.
- For the default BOT profile, make the action specific: `开始创建 OpenClaw BOT`.

### UX-007: Connection info is raw JSON instead of a setup card

Priority: P2 UX

Observed State:

- `/connect {bot_id}` returns raw JSON in a code block.
- The copy button copies the whole block.
- The raw JSON also appears in the conversation list preview, including token-like content.

Why It Matters:

- Developers can parse JSON, but the product task is "copy the right fields and connect a bot".
- The token is revealed once, so the UI should make the required copy/save behavior explicit.
- Raw JSON in the conversation preview makes the nav list noisy and exposes sensitive-looking content in a secondary surface.

Recommended Design:

- Render connection info as a setup card:
  - `BOT ID` with copy button
  - `Gateway URL` with copy button
  - `Token` with copy button and one-time warning
  - `Protocol Version`
  - `Install Command`
- Add warning text: `token 仅展示一次，请立即复制保存`.
- Put raw JSON behind `查看原始 JSON`.
- Use safe conversation preview text: `连接信息已生成，请复制 token 完成接入`.

Screenshot:

`/Users/baiyu/workspaces/gitlab/openim/.qa-artifacts/ux-walk-connect-json.jpg`

### UX-008: Login page is clean but lacks internal-product context

Priority: P3 UX

Observed State:

- Login form contains brand, login/register segmented control, and required fields.
- Empty submit validation appears under fields.
- There is no product subtitle, environment hint, or explanation of who should register.

Why It Matters:

- This is an internal IM/BOT Gateway, so users need quick context: employee login, local dev, staging, or production.
- Registration asks for `工号` and `姓名`, but the page does not explain account expectations.

Recommended Design:

- Add a compact subtitle under `OpenIM`: `员工助手接入与内部消息工作台`.
- For dev/staging, show a small environment badge such as `Local Dev`.
- Add helper text only where it reduces form errors, for example `使用员工账号登录`.
- Keep the form simple; do not turn this into a marketing landing page.

Screenshot:

`/Users/baiyu/workspaces/gitlab/openim/.qa-artifacts/ux-walk-login.jpg`

### UX-009: Conversation list previews need content-specific formatting

Priority: P3 UX

Observed State:

- After `/new-bot`, the default BOT conversation preview shows the full command result.
- After `/connect`, the preview shows raw JSON.

Why It Matters:

- A conversation list should help users identify the thread, not display long operational payloads.
- Long previews reduce scanability and make the middle panel feel cluttered.

Recommended Design:

- Normalize previews by message type:
  - Command success: `BOT 已创建`
  - Connection info: `连接信息已生成`
  - Error: `发送失败，请重试`
- Limit preview text to one line and strip raw JSON/code blocks.
- Add a small `默认` or `系统` badge beside default BOT.

### UX-010: Visual hierarchy is serviceable but too uniform for the main workflow

Priority: P3 UX

Observed State:

- The three-column layout is restrained and generally suitable for an operational tool.
- Most rows, panels, and empty states have similar visual weight.
- The primary workflow, default BOT setup, does not stand out.

Why It Matters:

- Quiet enterprise UI is appropriate, but users still need a clear primary path.
- Equal-weight panels make the app feel like a generic chat shell instead of an assistant onboarding console.

Recommended Design:

- Make default BOT onboarding the first-viewport signal for new users.
- Replace generic guide copy with direct actions.
- Use status chips and concise labels to improve scanning without decorative clutter.

## Recommended UI/UX Direction

The strongest direction is to make OpenIM feel less like a generic chat shell and more like a focused employee-assistant onboarding console.

Recommended first iteration:

1. First login opens a setup-focused default BOT state with `/new-bot` as a visible primary action.
2. Default BOT setup outputs render as structured cards, not raw chat bubbles.
3. Contact and BOT profiles use readiness banners and state-specific CTAs.
4. Contacts get search and relationship grouping before more features are added.
5. Mobile gets a real navigation model instead of hiding the sidebars.

Suggested page model:

- Left rail: app/global nav and account only.
- Middle panel: searchable list with tabs for `会话`, `AI`, and `联系人`.
- Main panel: either `Setup Card`, `Profile`, or `Conversation`.
- Setup cards own the BOT connection workflow: create slot, copy token, connect gateway, verify status.

## Release Assessment

The core backend and plugin paths are mostly healthy, but release readiness is blocked by the failing P0 script unless the team intentionally retires or updates that script. The remaining issues are not hard blockers for the backend, but they materially affect user confidence in the frontend state model and should be fixed before broader usage.

Recommended priority:

1. Align `npm run e2e:p0` and README with the current conversation creation flow, or restore automatic default BOT conversation creation.
2. Fix timezone serialization/parsing for user presence.
3. Refresh selected user profile state after friend request success.
4. Gate OpenClaw BOT chat entry and sending based on binding and online status.
5. Clear auth errors when switching login/register mode.
6. Add first-run empty-state CTA and mobile navigation before broader user testing.
7. Add command chips and structured connection cards to reduce setup friction.
