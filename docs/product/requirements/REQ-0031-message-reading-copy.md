# REQ-0031 Message Reading Width and Copy Action

## Background

After REQ-0024, assistant messages are still visually narrower than expected on desktop. Assistant and system responses often contain long Markdown, HTML fragments, reports, tables, and code. These messages should use the available reading area and be easy to copy.

## Requirements

- Non-user messages must use the available chat reading width on desktop.
- User messages must remain right aligned and compact.
- Non-user text/rich messages must provide a copy action.
- Copy must use the original message content, not the rendered DOM text.
- Rich rendering, long-message collapse, tables, and code block overflow must remain stable.

## Acceptance Criteria

- Assistant/system bubbles fill the available message column width on desktop.
- User bubbles remain narrower than assistant/system bubbles.
- A visible copy control is available on non-user rich/text messages.
- Copy success and failure feedback is shown.
- `npm run test -w apps/web` passes.
- `npm run build -w apps/web` passes.
