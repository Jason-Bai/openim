# REQ-0024 Technical Design: Chat Workspace UI Optimization

Status: technical design approved on 2026-05-27.

Issue: https://github.com/Jason-Bai/openim/issues/24

PRD: `docs/product/requirements/REQ-0024-chat-workspace-ui.md`

UX: `docs/product/designs/REQ-0024-chat-workspace-ui.md`

Registry: `docs/workflow/active/REQ-0024-chat-workspace-ui.yml`

## 1. Current Implementation

The web app is a React/Vite app under `apps/web`.

Relevant current files:

- `apps/web/src/pages/App.tsx`
- `apps/web/src/components/AppSidebar.tsx`
- `apps/web/src/components/MessageRenderer.tsx`
- `apps/web/src/components/MessageContent.tsx`
- `apps/web/src/components/CollapsibleMessage.tsx`
- `apps/web/src/api/openim.ts`
- `apps/web/src/styles.css`

Current UI structure:

- `ChatPage` owns menu selection, selected profile/conversation, input state, optimistic messages, and all mutations.
- `AppSidebar` renders the primary navigation and account/logout controls.
- `SessionsList` and `ContactsPanel` render the middle list panel.
- `ConversationChat` renders header, message list, scroll-to-bottom button, notices, quick commands, and composer.
- `MessageRenderer` handles code, plain user messages, and rich assistant messages.

Current limitations:

- The CSS uses a fixed desktop grid: `168px 320px 1fr`.
- The mobile media query stacks sidebar, list panel, and chat panel vertically.
- Conversation previews reuse `conversation.last_message` directly.
- Chat header displays `conversation.target_id` as the subtitle.
- No explicit mobile list/chat view state exists.

## 2. Proposed Frontend Architecture

Keep this as a frontend-only UI requirement. Do not add backend APIs or migrations.

Introduce small, local UI helpers rather than a broad app rewrite:

- `formatConversationPreview(conversation)` converts raw last-message content into a plain text preview.
- `conversationStatusText(conversation)` returns user-facing status/type text for headers and list metadata.
- `conversationTechnicalDetail(conversation)` returns secondary metadata, such as `BOT_ID`, for detail/copy affordances.
- `useIsNarrowViewport()` or equivalent state detects the mobile layout breakpoint in React when the UI needs behavior changes, not just CSS changes.

Component boundary recommendation:

- Keep `AppSidebar` as the primary navigation component.
- Add or extract `ConversationListItem` for session/contact list rows if the implementation starts adding too much logic inside `SessionsList`.
- Add or extract `ConversationHeader` for title/status/back/detail behavior.
- Keep `ConversationChat` as the owner of message scroll state and composer behavior.

Do not introduce a router for this requirement. Use local state to switch between mobile list and chat surfaces.

## 3. Data And State Changes

No backend data model change is required.

Frontend state additions:

- Track whether the mobile layout is in list state or detail state.
- On mobile conversation select, transition to detail state.
- On mobile back, return to list state and keep the selected conversation in state.
- On desktop, both list and detail surfaces remain visible.

Candidate state:

```ts
const [mobileSurface, setMobileSurface] = useState<"list" | "detail">("list");
```

Behavior:

- Selecting a conversation sets selected conversation and moves mobile surface to `detail`.
- Selecting a profile from contacts sets selected profile and moves mobile surface to `detail`.
- Changing primary menu on mobile returns to `list`.
- Desktop ignores `mobileSurface` for visibility.

Browser history integration is intentionally deferred.

## 4. Preview Formatting

Conversation previews should not expose raw Markdown.

Implement deterministic client-side formatting:

1. Strip fenced code blocks down to a short marker or first line.
2. Remove Markdown heading markers, table separators, task checkbox markers, emphasis markers, and inline code backticks.
3. Collapse whitespace to one line.
4. Truncate to a fixed character count.

This helper should be unit-testable as a pure function. It can live in a small utility module if tests are added.

Do not add AI-generated summaries.

## 5. Header And Metadata

Replace the primary header subtitle from `conversation.target_id` to user-facing status text:

- Default BOT: `System assistant · Online`
- OpenClaw BOT connected: `OpenClaw assistant · Connected`
- OpenClaw BOT disconnected: `OpenClaw assistant · Disconnected`
- User conversation: relationship/presence text when available from conversation data; otherwise `Direct message`

Technical IDs should move behind a detail affordance. A minimal first implementation can use an Ant Design tooltip or popover plus copy button. If copy interaction adds too much scope, keep the ID visible in a secondary muted detail row, not as the primary subtitle.

## 6. Responsive Layout

CSS should keep the desktop grid, but mobile should become stateful rather than stacked:

- Desktop:
  - `.shell` remains a three-column grid.
  - `AppSidebar`, list panel, and chat panel are visible.
- Mobile:
  - Primary navigation becomes a compact top bar.
  - List panel is visible only in list state.
  - Chat/profile/guide panel is visible only in detail state when applicable.
  - Chat header includes a back button.
  - Composer remains fixed in the chat grid bottom row.

Avoid absolute-positioned full-screen overlays for the main app unless required. Prefer CSS classes derived from state, such as:

- `.shell.mobileList`
- `.shell.mobileDetail`
- `.chatMobileBackButton`

## 7. Rich Message Refinement

Keep the current renderer and sanitizer.

CSS refinements:

- On mobile, reduce message-list side padding.
- Let assistant rich bubbles use the full available width.
- Keep code blocks and tables horizontally scrollable within the bubble.
- Keep expand/collapse at the top.

No changes to sanitization schema are required unless visual changes reveal a rendering bug.

## 8. Accessibility

Required:

- Mobile back button with accessible name, such as `返回会话列表`.
- Conversation list items should be buttons or keyboard-focusable elements with selected state.
- Status dots must be accompanied by text somewhere in the item or header.
- Detail/copy controls must have accessible names.
- Existing `滚动到底部` button accessible name should remain.

## 9. Files Likely Affected

- `apps/web/src/pages/App.tsx`
- `apps/web/src/components/AppSidebar.tsx`
- `apps/web/src/styles.css`
- Optional new component: `apps/web/src/components/ConversationHeader.tsx`
- Optional new component: `apps/web/src/components/ConversationListItem.tsx`
- Optional helper: `apps/web/src/utils/conversationDisplay.ts`
- Optional tests for helper functions if the current test setup supports them.

## 10. Test Strategy

Required verification:

```bash
npm run test -w apps/web
npm run build -w apps/web
```

Browser QA:

- Desktop `1280x720`
- Desktop `1440x900`
- Mobile `390x844`

Checks:

- Desktop shows stable navigation/list/chat layout.
- Mobile list state does not show chat content.
- Mobile detail state does not show the list as primary content and has a back control.
- Conversation previews are plain text.
- Header subtitle is user-facing status, not raw BOT ID.
- Long rich messages remain collapsible and do not overflow horizontally.
- Composer remains reachable.

## 11. Rollout And Rollback

Rollout follows normal branch promotion:

```text
feature/24-chat-workspace-ui -> develop -> test -> main
```

Rollback:

- Revert the feature PR if layout regressions are found.
- Because this requirement is frontend-only, backend rollback is not needed.

## 12. Risks

- `App.tsx` is already large. Keep extraction focused on the surfaces being changed.
- The mobile state model can conflict with existing selected profile/conversation state if not handled deliberately.
- Preview formatting can become too clever. Keep it deterministic and small.
