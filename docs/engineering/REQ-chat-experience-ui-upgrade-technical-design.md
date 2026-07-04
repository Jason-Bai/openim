# REQ-chat-experience-ui-upgrade Technical Design

Date: 2026-05-27
Status: Technical design draft for review
Requirement: `docs/superpowers/specs/2026-05-27-chat-experience-ui-upgrade-design.md`
Registry: `docs/workflow/active/REQ-chat-experience-ui-upgrade.yml`

## 1. Summary

This design implements the approved chat experience PRD as a frontend-first change. It keeps the current FastAPI conversation contracts unchanged and introduces focused React boundaries for:

1. Enterprise IM sidebar shell.
2. Reusable message rendering with Markdown, safe HTML, and long-content folding.
3. Conversation scroll-to-bottom behavior.

The highest-risk area is rich content rendering. The design uses a sanitizer-backed Markdown pipeline and does not render arbitrary HTML.

## 2. Current State

Relevant frontend files:

- `apps/web/src/pages/App.tsx`
- `apps/web/src/styles.css`
- `apps/web/src/api/openim.ts`
- `apps/web/src/components/CopyableCodeBlock.tsx`

Current behavior:

- `ChatPage` owns shell layout, navigation, selected view, message sending, and cache updates in one large file.
- `ConversationChat` renders message text directly in `.bubble`.
- `content_type` currently supports only `"text"` and `"code"` in the frontend type.
- `.messageList` is a basic scroll container with no bottom tracking.
- `.mainMenu` is a dark vertical sidebar with Ant Design text buttons.

## 3. Architecture

### 3.1 Frontend Component Boundaries

Create small focused components under `apps/web/src/components/`:

```text
components/
  AppSidebar.tsx
  MessageRenderer.tsx
  MessageContent.tsx
  CollapsibleMessage.tsx
  ScrollToBottomButton.tsx
  useConversationScroll.ts
```

Responsibilities:

- `AppSidebar`: presentational shell navigation, account display, logout action.
- `MessageRenderer`: chooses message display path based on `content_type` and sender.
- `MessageContent`: Markdown + safe HTML rendering.
- `CollapsibleMessage`: rendered-height measurement and expand/collapse state.
- `ScrollToBottomButton`: bottom-right button and optional `新消息` indicator.
- `useConversationScroll`: scroll container ref, near-bottom tracking, auto-scroll decisions, new-message indicator state.

Keep data fetching, mutations, and selected-view state in `App.tsx` for this iteration. Do not introduce a global chat provider until code pressure requires it.

### 3.2 No Backend Contract Change In First Slice

Do not add backend fields in the first implementation.

Initial strategy:

- Continue receiving messages as `ConversationMessage.content_type: "text" | "code"`.
- Treat normal text messages as Markdown-capable content.
- Support raw safe HTML inside Markdown by parsing and sanitizing it in the frontend.
- Keep `content_type === "code"` on the existing `CopyableCodeBlock` path.

Reasoning:

- The current backend stores only content string plus `content_type`.
- The PRD does not require format authoring or explicit rich message metadata.
- Adding format metadata now would touch backend models, tests, and migration scope before the product need proves it is required.

Future extension:

```ts
content_type: "text" | "code" | "markdown" | "html"
```

or:

```ts
content_format: "plain" | "markdown" | "safe_html"
```

This should be handled in a later requirement if rendering ambiguity becomes a real issue.

## 4. Rich Message Rendering

### 4.1 Dependencies

Add frontend dependencies:

```text
react-markdown
remark-gfm
rehype-raw
rehype-sanitize
```

Purpose:

- `react-markdown`: render Markdown as React elements.
- `remark-gfm`: enable tables, task-list-like syntax, and common GitHub-flavored Markdown behavior.
- `rehype-raw`: parse raw HTML embedded in Markdown.
- `rehype-sanitize`: sanitize parsed HTML against an allowlist.

Security rule:

- Use `rehype-raw` only when followed by `rehype-sanitize`.
- Never use `dangerouslySetInnerHTML` for user or assistant content.

### 4.2 Sanitizer Policy

Define a local sanitizer schema in `MessageContent.tsx` or a small helper file if it gets long.

Allowed tags:

```text
p, br, strong, em, u, s,
ul, ol, li,
blockquote,
code, pre,
table, thead, tbody, tr, th, td,
a
```

Allowed attributes:

- `a.href`
- `a.title`
- table alignment attributes only if needed by the selected library and safe.

Disallowed:

- `script`
- `style`
- `iframe`
- `object`
- `embed`
- any `on*` event attribute
- `javascript:` URLs
- inline style attributes

Links:

- Render `a` through a custom component that sets:
  - `target="_blank"`
  - `rel="noreferrer noopener"`

### 4.3 Renderer Behavior

`MessageRenderer` input:

```ts
type MessageRendererProps = {
  message: ConversationMessage;
};
```

Behavior:

- `content_type === "code"`: render existing `CopyableCodeBlock`.
- Otherwise:
  - Render `CollapsibleMessage`.
  - Inside it render `MessageContent`.

The renderer should not own message list scrolling, sending, data fetching, or mutation logic.

### 4.4 Markdown Styling

Use scoped CSS classes, for example:

```css
.messageContent
.messageContent pre
.messageContent code
.messageContent table
.messageContent blockquote
```

Requirements:

- Code blocks use an internal horizontal scroll and do not expand page width.
- Tables are wrapped or styled so they can scroll horizontally inside the bubble.
- Paragraph and list spacing is compact enough for chat.
- User-sent messages remain readable on the blue bubble. If rich rendering on user bubbles creates contrast issues, the first implementation may render user messages as escaped plain text while bot/system messages use rich rendering.

Recommended decision:

- Apply rich rendering to bot/system messages.
- Keep user messages as plain text in this first implementation unless manual QA proves Markdown in user messages is needed.

Reasoning:

- The user requirement is about OpenClaw employee-assistant replies.
- User rich rendering inside blue bubbles increases contrast and CSS complexity.

## 5. Long Message Folding

### 5.1 Component

`CollapsibleMessage` wraps rendered content and measures actual rendered height.

Props:

```ts
type CollapsibleMessageProps = {
  collapsedHeight?: number;
  children: ReactNode;
};
```

Default:

```text
collapsedHeight = 360
```

Behavior:

1. Render content normally in a measuring container.
2. After layout, if `scrollHeight > collapsedHeight`, mark it collapsible.
3. If collapsible and not expanded:
   - Show `展开全文` at the top.
   - Limit content wrapper height to `collapsedHeight`.
   - Hide overflow.
4. If expanded:
   - Show `收起` at the top.
   - Remove height limit.

### 5.2 Measurement Details

Use `ResizeObserver` when available so images, tables, or fonts can update measured height after initial render.

Fallback:

- Run measurement in `useLayoutEffect`.

State:

- Per-message expanded state is local to each rendered message component.
- Do not persist expanded/collapsed state across sessions in this requirement.

Performance:

- Avoid measuring every scroll event.
- Measurement happens on content resize, not on message-list scrolling.

### 5.3 Scroll Interaction

When a user clicks `收起`, the message may become much shorter.

Handling:

- Let browser layout naturally adjust.
- Do not force-scroll to bottom.
- If technical implementation finds large jumps problematic, scroll the collapsed message's top into view only when the collapse action would move it above the viewport.

This refinement is optional for the first implementation.

## 6. Scroll-To-Bottom Behavior

### 6.1 Hook

`useConversationScroll` owns bottom tracking.

Inputs:

```ts
type UseConversationScrollInput = {
  messageCount: number;
  lastMessageId: string | undefined;
  lastMessageSenderType: ConversationMessage["sender_type"] | undefined;
};
```

Outputs:

```ts
{
  scrollRef: RefObject<HTMLDivElement>;
  isNearBottom: boolean;
  hasNewMessages: boolean;
  scrollToBottom: () => void;
}
```

### 6.2 Near-Bottom Threshold

Initial threshold:

```text
80px
```

Near bottom means:

```text
scrollHeight - scrollTop - clientHeight <= 80
```

### 6.3 Auto-Scroll Rules

Auto-scroll when:

- The user is already near the bottom and a new message arrives.
- The last new message is sent by the current user.
- The conversation changes and messages are first loaded.

Do not auto-scroll when:

- The user has manually scrolled away from the bottom.
- A bot/system message arrives while the user is reading older content.

When not auto-scrolling:

- Set `hasNewMessages = true`.
- Show `ScrollToBottomButton` with `新消息`.

Clicking the button:

- Scrolls to bottom.
- Clears `hasNewMessages`.

### 6.4 Event Handling

Use passive scroll listener or React `onScroll` with minimal state updates.

Avoid setting state on every scroll pixel:

- Only update state when near-bottom boolean changes.
- Use refs for transient values such as previous message ID.

## 7. Sidebar Redesign

### 7.1 Layout

Keep existing shell grid concept:

```css
.shell {
  grid-template-columns: sidebar list chat;
}
```

But update sidebar visual treatment:

- Light background.
- Subtle right border.
- Clear brand block.
- Navigation buttons styled as stable IM nav items.
- Account area separated from primary navigation.

Suggested dimensions:

- Sidebar width: 88px to 112px if using icon-first vertical nav.
- If keeping icon + text in a wider nav, use 168px to avoid wrapping.

Recommended first implementation:

- Keep current 168px width to reduce layout risk.
- Use light enterprise IM styling and improved active state.
- Revisit compact icon-first sidebar later if needed.

### 7.2 Component API

```ts
type AppSidebarProps = {
  menu: MenuKey;
  username: string;
  onMenuChange: (menu: MenuKey) => void;
  onLogout: () => void;
};
```

`AppSidebar` should be presentational:

- No data fetching.
- No selected conversation logic.
- Receives callbacks from `ChatPage`.

### 7.3 Accessibility

Requirements:

- Navigation region has an accessible label.
- Buttons have visible text and stable accessible names.
- Current item uses visual active state and `aria-current` if implemented as links or nav buttons.
- Logout button remains keyboard reachable.

## 8. CSS Strategy

Keep the current single `apps/web/src/styles.css` for this requirement, but organize additions by sections:

```css
/* Sidebar */
/* Message renderer */
/* Collapsible message */
/* Scroll controls */
```

Do not introduce CSS modules or a styling framework in this change.

Color guidance:

- Avoid a one-note dark slate UI.
- Use light neutral surfaces with controlled blue accent for active state.
- Maintain WCAG-readable contrast for body text, secondary text, and buttons.

Responsive:

- Preserve existing <= 860px layout behavior unless small CSS adjustments are needed.
- Verify no horizontal overflow after tables/code blocks are added.

## 9. Implementation Slices

This technical design supports three GitHub Issues after approval:

### Issue 1: Sidebar Redesign

Files likely touched:

- `apps/web/src/pages/App.tsx`
- `apps/web/src/components/AppSidebar.tsx`
- `apps/web/src/styles.css`

Verification:

- `npm run build -w apps/web`
- Browser QA desktop and <= 860px.

### Issue 2: Message Renderer And Folding

Files likely touched:

- `apps/web/package.json`
- `package-lock.json`
- `apps/web/src/api/openim.ts` if type comments or future type widening are needed.
- `apps/web/src/pages/App.tsx`
- `apps/web/src/components/MessageRenderer.tsx`
- `apps/web/src/components/MessageContent.tsx`
- `apps/web/src/components/CollapsibleMessage.tsx`
- `apps/web/src/styles.css`

Verification:

- `npm run build -w apps/web`
- Manual Markdown and safe HTML cases.
- Unsafe HTML does not execute.
- Long message folds with top `展开全文`.

### Issue 3: Scroll-To-Bottom Affordance

Files likely touched:

- `apps/web/src/pages/App.tsx`
- `apps/web/src/components/ScrollToBottomButton.tsx`
- `apps/web/src/components/useConversationScroll.ts`
- `apps/web/src/styles.css`

Verification:

- `npm run build -w apps/web`
- Browser QA with long conversation.
- Validate new incoming message while away from bottom.

## 10. Testing And QA

Automated verification:

```bash
npm run build -w apps/web
```

If dependencies are added:

```bash
npm install
npm run build -w apps/web
```

Manual browser QA cases:

1. Sidebar visual state:
   - Open conversations.
   - Open contacts.
   - Confirm active state and account area.
2. Markdown:
   - headings, list, inline code, code block, table, link.
3. Safe HTML:
   - paragraph, list, table, link.
4. Unsafe HTML:
   - `<script>`, `onerror`, `javascript:` link.
   - Expected: no execution, no unsafe interaction.
5. Long message:
   - Bot/system message over 360px.
   - Confirm top `展开全文`, expand, top `收起`, collapse.
6. Scroll:
   - Open long conversation.
   - Scroll upward.
   - Confirm bottom-right button.
   - Receive/send new message.
   - Confirm non-interrupting behavior and button clearing.
7. Responsive:
   - <= 860px width.
   - Ensure chat input remains usable and no page-level horizontal overflow.

## 11. Risks

### 11.1 Sanitizer Misconfiguration

Risk:

- Unsafe HTML could render if plugin order or schema is wrong.

Mitigation:

- Keep `rehype-raw` directly followed by `rehype-sanitize`.
- Add explicit manual QA cases.
- Avoid `dangerouslySetInnerHTML`.

### 11.2 Bundle Growth

Risk:

- Markdown and sanitizer libraries increase frontend bundle size.

Mitigation:

- Keep dependency set small.
- Do not add a full rich-text editor.
- If bundle growth is too high after measurement, lazy-load message renderer for bot/system messages in a follow-up optimization.

### 11.3 Large `App.tsx` Continues Growing

Risk:

- Current `App.tsx` already owns many responsibilities.

Mitigation:

- Extract presentational and behavior components listed in section 3.1.
- Do not add more renderer or scroll logic inline to `ConversationChat`.

### 11.4 Scroll State Race Conditions

Risk:

- WebSocket messages, optimistic messages, and query refetches may all update the message list.

Mitigation:

- Track latest message ID.
- Deduplicate messages through existing cache merge.
- Auto-scroll only after DOM updates using effect timing tied to latest message ID.

## 12. Open Technical Questions For Review

1. Should user-sent text also render as Markdown in this release, or should rich rendering apply only to bot/system messages first?
2. Should the collapsed height stay at 360px after QA, or should desktop and mobile use different thresholds?
3. Should the message renderer include a small visual label for folded content in group chats later, or keep the same simple `展开全文` control?

Recommended answers for this release:

1. Bot/system messages only.
2. Start with 360px globally and adjust only if QA shows issues.
3. Keep the same simple control; group-specific labels belong in the future group feature.
