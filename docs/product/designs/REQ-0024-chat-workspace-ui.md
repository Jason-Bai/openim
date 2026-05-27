# REQ-0024 UX Design: Chat Workspace Information Architecture

## Status

Draft for UX review.

## Evidence From UI Review

Observed against the released `origin/main` baseline on 2026-05-27.

| Priority | Surface | Observed Problem | User Impact |
|---|---|---|---|
| P0 | Mobile shell | Brand, primary nav, username, and logout crowd into one row; list and chat content stack vertically. | Users lose orientation and must scroll through navigation/list content before reading chat. |
| P1 | Conversation list | Last-message previews expose raw Markdown such as headings and table syntax. | Users cannot quickly scan what a conversation is about. |
| P1 | Chat header | Technical BOT ID is shown as the main subtitle. | Users see implementation detail before useful status. |
| P1 | Empty states | Guide states are sparse and action-focused without enough context. | New or returning users may not know current connection state or next best action. |
| P2 | Rich messages | Long assistant responses render correctly but carry heavy document-card visual weight, especially on mobile. | Reading is functional but dense; conversation flow feels less like chat. |

## Design Principles

- Prioritize one primary surface per viewport: list or chat on mobile, three coordinated areas on desktop.
- Use business language first and technical metadata second.
- Make scanning cheap: title, status, preview, and recency should be visible without reading raw content.
- Preserve density for enterprise use, but avoid cramming unrelated controls into the same row.
- Keep controls familiar: back arrow for mobile return, status dot/text for presence, icon button for scroll-to-bottom, text link for expand/collapse.

## Desktop Layout

Desktop keeps a three-area model:

1. Primary navigation: compact product brand, Sessions, Contacts, and an account menu.
2. List panel: mode title, optional search slot, grouped list items, and clean previews.
3. Main panel: chat header, message stream, notices/quick commands, and composer.

The primary navigation should remain visually quiet. The account area should not consume a large vertical block; long usernames should truncate with title text or move into a menu-style button.

The list panel should become a scanning surface. Each item should show:

- Icon or avatar.
- Status indicator.
- Title.
- Plain-text preview.
- Optional secondary metadata such as assistant type or connection state.

## Mobile Layout

Mobile should switch to a two-screen state model:

- List state: primary navigation and conversation/contact list are visible. Chat content is hidden.
- Chat state: chat header, messages, and composer are visible. List panel is hidden.

The chat state header should include:

- Back button to return to list.
- Conversation title.
- Status text such as "OpenClaw assistant · Online" or "Disconnected".
- Optional more/detail action for technical metadata.

The mobile account/logout controls should not share the same row with all navigation labels. Acceptable options:

- Move account into an icon/menu button.
- Collapse primary navigation to icon+active label.
- Keep logout inside the account menu.

## Conversation Header

Header hierarchy:

1. Conversation title.
2. User-facing status and type.
3. Optional technical metadata behind a detail affordance.

Examples:

- `OpenClaw 员工助手`
- `OpenClaw assistant · Connected`
- Detail: `BOT_ID: bot_...`

For users, show relationship or presence before IDs. For system/default bots, show `System assistant · Online`.

## Empty And Guide States

Guide states should answer three questions:

- What is this area?
- What is the current state?
- What should I do next?

Recommended copy direction:

- Sessions empty or no selection: "选择一个会话开始，或通过默认 BOT 创建 OpenClaw 助手连接。"
- Contacts empty or no selection: "选择联系人或 AI，查看资料并开始聊天。"
- OpenClaw disconnected: "OpenClaw 助手当前未连接。普通聊天不可用，后台可重新连接。"

Do not add the admin console in this requirement. If an admin entry is shown, it should be disabled or clearly marked as future scope unless the backend/admin feature is approved separately.

## Rich Message Hierarchy

Keep the existing safe renderer and collapse behavior. Refine presentation:

- Mobile message bubbles should use full available width with smaller side gutters.
- Long rich messages should show the expand/collapse action at the top.
- Headings should remain compact.
- Code blocks and tables should scroll horizontally within the bubble.
- Links should remain visually distinct and keyboard focusable.

Do not add AI summary generation in this requirement. If summaries are needed, use deterministic preview extraction from content text only.

## States

Required visible states:

- List loading.
- Empty sessions.
- Empty contacts.
- Active conversation.
- OpenClaw connected.
- OpenClaw disconnected.
- Message sending.
- Long message collapsed.
- Long message expanded.
- Away from bottom with scroll-to-bottom button visible.

## Accessibility

- Primary navigation buttons need accessible names and active state.
- Mobile back button needs an accessible name.
- Conversation list items should be keyboard focusable and indicate selected state.
- Expand/collapse buttons should announce the correct action.
- Scroll-to-bottom button should keep the `滚动到底部` accessible name.
- Color-only status dots must be paired with status text somewhere in the item or header.

## Responsive Verification

Verify at:

- Desktop: `1280x720`, `1440x900`.
- Mobile: `390x844`.

Checks:

- No overlapping text or controls.
- No raw Markdown preview in list items.
- Mobile list state and chat state are mutually exclusive.
- Chat composer remains reachable at bottom.
- Long rich messages do not overflow the viewport horizontally.
