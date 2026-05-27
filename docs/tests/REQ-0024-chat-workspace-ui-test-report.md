# REQ-0024 Chat Workspace UI Test Report

Date: 2026-05-27

Branch: `feature/24-chat-workspace-ui`

Issue: https://github.com/Jason-Bai/openim/issues/24

## Command Verification

Run from repository root.

```bash
npm run test -w apps/web
```

Result: Passed.

Coverage:

- TypeScript project check.
- Vitest helper tests for conversation preview formatting, empty preview fallback, technical identifier preservation, and business-facing status/technical detail text.

Observed warning:

- Vitest/Vite prints a React plugin deprecation warning about `esbuild`/`oxc` options. The test run passes.

```bash
npm run build -w apps/web
```

Result: Passed.

Observed warning:

- Vite reports the main bundle is larger than 500 kB after minification. This warning existed before this requirement and is not release-blocking for this UI scope.

## Browser QA

Local preview:

```bash
npm run dev --workspace apps/web -- --host 127.0.0.1 --port 5182
```

QA account:

- Username: `uiqa_1779844422253`
- Password: `secret123`

### Desktop

Viewports:

- `1280x720`
- `1440x900`

Result: Passed.

Checks:

- Three-area desktop layout remains visible: primary navigation, conversation list, chat content.
- Conversation list previews display plain text instead of raw Markdown heading/table syntax.
- Technical identifiers with underscores remain intact in previews.
- Chat header shows `OpenClaw assistant · Connected` instead of raw BOT ID as the primary subtitle.
- Copy technical information button is present with accessible name `复制会话技术信息`.
- Long rich messages remain collapsible and readable.

### Mobile

Viewport:

- `390x844`

Result: Passed.

Checks:

- List state shows primary navigation and conversation list only.
- Chat content is hidden in list state.
- Selecting a conversation switches to detail state.
- Detail state hides the conversation list as primary content.
- Detail state exposes accessible back button `返回会话列表`.
- Back button returns to the conversation list.
- Composer remains reachable at the bottom of the detail state.
- Rich message bubbles use available mobile width and do not overflow horizontally in observed content.

## Residual Risks

- Browser history integration for mobile back behavior is intentionally deferred.
- Unread count and notification semantics are intentionally deferred.
- The app still uses a large `App.tsx`; this change only extracts the conversation header and display helpers where needed.
- Bundle chunk-size optimization remains a separate future performance task.
