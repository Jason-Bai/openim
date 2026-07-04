# OpenIM UI/UX QA Optimization Report

Date: 2026-05-27
Tester role: QA + UI/UX reviewer, executed with Chrome plugin
Environment:

- Frontend: http://localhost:5173/
- Backend: http://localhost:8080/
- Browser viewport during Chrome test: 1920 x 929
- Test account: `uiqa_1779844422253`

## 1. How To Staff Page Testing

For each UI requirement, use a small role split instead of only developer self-test:

| Role | Responsibility | Output |
| --- | --- | --- |
| Product reviewer | Confirms user goal, priority, scope, and acceptance criteria. | PRD comments / acceptance checklist |
| UI/UX reviewer | Reviews layout hierarchy, information architecture, density, responsive behavior, empty states, and interaction clarity. | UI optimization notes / annotated screenshots |
| QA tester | Executes core flows, edge cases, regression checks, and bug classification. | Test report / bug list |
| Developer self-reviewer | Checks implementation consistency, state refresh, error handling, and test coverage. | Code review notes |

For this project, a practical workflow is:

1. PRD confirmed.
2. Technical design confirmed.
3. Create GitHub Issues by minimum independent feature.
4. Development branch implementation.
5. Developer self-test.
6. Page tester runs Chrome UI/UX QA before PR.
7. Code review and CI.
8. Product acceptance after merge to test/staging branch.

## 2. Test Scope

Covered:

- Login page layout and validation.
- Register and auto-login.
- Main shell layout.
- Session guide empty state.
- Default BOT conversation creation.
- Message sending with `/help`.
- BOT slot creation with `/new-bot`.
- Contacts panel and profile panel.
- Add friend interaction.
- OpenClaw BOT offline profile state.
- Refresh persistence.
- Console error scan.

Not fully covered:

- Narrow mobile viewport in Chrome extension. The connected Chrome backend did not expose viewport override; responsive behavior was reviewed from CSS/code and desktop Chrome only.
- Real OpenClaw local bridge connected state.
- Multi-user friend accept/reject from the recipient side.

## 3. Evidence

Screenshots captured:

- `docs/tests/assets/2026-05-27-uiqa-01-login.png`
- `docs/tests/assets/2026-05-27-uiqa-02-desktop-guide.png`
- `docs/tests/assets/2026-05-27-uiqa-03-default-bot-chat.png`
- `docs/tests/assets/2026-05-27-uiqa-04-help-result.png`
- `docs/tests/assets/2026-05-27-uiqa-05-new-bot.png`
- `docs/tests/assets/2026-05-27-uiqa-06-contacts.png`
- `docs/tests/assets/2026-05-27-uiqa-07-user-profile.png`
- `docs/tests/assets/2026-05-27-uiqa-08-add-friend.png`
- `docs/tests/assets/2026-05-27-uiqa-09-openclaw-profile.png`
- `docs/tests/assets/2026-05-27-uiqa-10-after-reload.png`
- `docs/tests/assets/2026-05-27-uiqa-11-invalid-login.png`

Console scan after reload: no browser console errors or warnings observed.

## 4. Findings

### P1: `/new-bot` does not refresh contacts immediately

Observed:

- After sending `/new-bot`, the BOT is created and the conversation message shows the new BOT ID.
- Switching to Contacts immediately did not show the new OpenClaw BOT.
- After another mutation invalidated contacts, the BOT appeared in both AI and all contacts sections.

Impact:

- User follows the onboarding flow but cannot immediately find the newly created BOT in Contacts.
- This weakens confidence in whether `/new-bot` succeeded.

Recommendation:

- When default BOT command result creates, deletes, connects, or disconnects a BOT, invalidate/refetch `contacts` and `conversations`.
- If the command result can include structured metadata later, use metadata-driven cache updates instead of parsing command text.

### P2: Contacts information architecture duplicates default BOT and OpenClaw BOT

Observed:

- `默认 BOT` appears under both `已添加的 AI` and `全部联系人`.
- After refresh, the new OpenClaw BOT also appears under both sections.

Impact:

- Users may think these are separate entries.
- Selection state and profile navigation become harder to reason about.

Recommendation:

- Rename sections to clarify intent, for example `AI 助手` and `员工联系人`.
- Or keep `全部联系人` literal but visually group it as a complete directory and avoid repeating the same AI entries above.

### P2: Refresh resets selected conversation to guide while session list still shows existing conversation

Observed:

- After reload, the user remains logged in and the default BOT conversation is still in the session list.
- The right panel returns to the guide state instead of selecting the latest/active conversation.

Impact:

- Refresh persistence is technically present, but the task context is lost.
- For chat products, refresh usually preserves or restores the active thread.

Recommendation:

- Persist `selectedConversationId` locally per user.
- On reload, restore it when it still exists; otherwise select the most recent conversation.

### P2: Login submit button accessible name renders as `登 录`

Observed:

- The Ant Design button text is visually/semantically split as `登 录`.
- Role lookup by accessible name `登录` did not uniquely resolve; the button DOM text was `登 录`.

Impact:

- Minor accessibility/testability issue.
- Automation and screen-reader output may be less clean.

Recommendation:

- Add `aria-label="登录"` to the submit button or avoid typography that changes the accessible name.

### P3: Logout button touch target height is 24px

Observed:

- Desktop layout audit found `退出` button height is 24px.

Impact:

- Small target, especially risky on compact layouts.

Recommendation:

- Keep minimum interactive target height at least 32px, ideally 36-40px for app navigation.

### P3: Empty and loading states are too similar

Observed:

- Session list shows `暂无会话` while queries are still loading or when truly empty.
- Contacts are blank until data arrives; no explicit loading state.

Impact:

- Users cannot distinguish loading, empty, and failure states.

Recommendation:

- Add explicit loading skeleton/spinner for contacts and conversations.
- Add retry/error blocks for query failures.

## 5. Interaction Passes

Passed:

- Register + auto-login works.
- Invalid login shows `用户名或密码错误`.
- Default BOT conversation opens from the guide.
- `/help` sends and renders returned help text.
- `/new-bot` creates a BOT slot and displays the next command.
- Add friend updates profile relationship to `等待对方确认`.
- Offline OpenClaw BOT profile disables `发送消息` and explains why.
- Page reload keeps login state and backend-backed conversation list.
- No desktop overflow detected at 1920 x 929.

## 6. Recommended Next Issues

1. Fix BOT command cache refresh after `/new-bot`, `/delete-bot`, `/connect`, `/disconnect`.
2. Redesign contacts sections to remove duplicated AI entries or clarify grouping.
3. Restore selected conversation after page refresh.
4. Add explicit loading/error states for contacts, conversations, and messages.
5. Improve accessibility labels and minimum target sizes.
6. Add a responsive QA pass using a backend that supports viewport override, then validate <= 860px behavior.

