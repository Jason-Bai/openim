# REQ-0024: Chat Workspace Information Architecture And Responsive UI Optimization

## Status

Draft for requirement review.

## GitHub Issue

https://github.com/Jason-Bai/openim/issues/24

## Background

OpenIM now supports core chat workspace behaviors: sidebar navigation, safe rich assistant message rendering, long-message folding, and a scroll-to-bottom control. A UI review of the released `origin/main` baseline found that these capabilities work, but the workspace still reads like a functional prototype rather than a product-grade enterprise IM interface.

The largest gap is information architecture. Desktop has a three-column shell, but the list, header, empty state, and message hierarchy do not yet guide users through common work. Mobile currently compresses the desktop model into stacked regions, which makes the first screen crowded and makes conversation reading inefficient.

## Target Users

- Employees using OpenIM to chat with other employees and AI assistants.
- Employees connecting to an OpenClaw employee assistant.
- Product testers validating desktop and mobile chat flows.

## Problem Statement

Users need to scan conversations, understand assistant connection status, open a chat, read long assistant responses, and continue the conversation without fighting layout or raw technical details. The current UI makes these tasks harder because list previews expose raw Markdown, mobile navigation shows too many surfaces at once, and headers/empty states do not communicate product context.

## Goals

- Make the chat workspace feel like a coherent product surface rather than separate functional panels.
- Make mobile usable by separating conversation list and conversation detail views.
- Improve conversation scanning with clean previews, status, and hierarchy.
- Replace technical-first BOT details with user-facing status and optional technical detail.
- Keep rich assistant messages readable on desktop and mobile.

## Non-Goals

- Do not build the OpenClaw bridge auto-reconnect behavior in this requirement.
- Do not build a full BOT admin console.
- Do not change backend group chat behavior.
- Do not add backend message search or indexing.
- Do not redesign authentication.

## Requirements

### R1. Desktop Workspace Hierarchy

The desktop chat workspace should keep the primary navigation, conversation/contact list, and main content areas visually distinct. The list should support fast scanning, and the main content should clearly indicate the active conversation or next action.

### R2. Mobile List-To-Chat Model

On mobile widths, the UI should not show primary navigation, conversation list, and chat content as a long stacked page. Users should see either the list surface or the active conversation surface. Opening a conversation should provide a clear way back to the list.

### R3. Conversation List Preview Quality

Conversation previews should not expose raw Markdown syntax as the main scanning text. Long assistant messages should be converted to a concise plain-text preview with sensible truncation.

### R4. Business-Facing Conversation Header

Conversation headers should prioritize the conversation name, online/connection status, and assistant type. Technical IDs should be available only as secondary detail, such as a tooltip, detail row, or copied metadata action.

### R5. Empty And Guide States

Empty and guide states should explain where the user is, why no conversation is selected, and what the primary next step is. OpenClaw-related actions should distinguish normal chat actions from future admin/management actions.

### R6. Rich Message Reading Hierarchy

Rich assistant messages should remain safe and readable. Long-message folding should stay, but the message layout should reduce visual weight on mobile and support clear hierarchy for headings, paragraphs, code, tables, and links.

### R7. Accessibility And Responsive Quality

Navigation, list items, message controls, and scroll controls should have accessible names and usable focus states. Layout should be verified at desktop and mobile viewport sizes without text overlap or unreadable controls.

## Acceptance Criteria

- Desktop at `1280x720` and `1440x900` shows a stable three-area workspace without overlapping controls.
- Mobile at `390x844` shows either list or chat detail, not both stacked as primary content.
- Mobile conversation detail has a visible back affordance to return to the list.
- Conversation previews display plain text, not raw Markdown headings or table syntax.
- The active conversation header shows user-facing status before technical IDs.
- Empty state copy explains the next action and does not rely only on "打开默认 BOT".
- Long assistant messages remain collapsible and readable on mobile.
- Keyboard focus and screen-reader labels exist for primary navigation, back, send, expand/collapse, and scroll-to-bottom controls.

## Risks

- A route-like mobile model may require additional UI state and careful browser history decisions.
- Cleaning message previews may introduce duplicated text-processing logic if not centralized.
- Improving empty states could drift into admin-console scope if not constrained.

## Open Questions

- Should mobile back behavior integrate with browser history, or only with in-app state?
- Should the conversation list include timestamps in this requirement?
- Should technical BOT IDs be copyable from the header detail, or only hidden visually?
- Should unread counts be included now, or deferred until notification semantics are designed?
