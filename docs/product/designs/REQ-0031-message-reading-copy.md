# REQ-0031 UX Design

## Message Width

Assistant and system messages are treated as reading surfaces. On desktop, they should stretch across the available chat content area so long reports, Markdown lists, tables, and code samples have more usable space.

User messages remain compact and right aligned. This keeps conversational rhythm clear and avoids making short user inputs feel oversized.

## Copy Action

Non-user rich/text messages expose a small icon button in the top-right corner of the message bubble. The button copies the original message body and shows success or failure feedback through the existing Ant Design message toast.

The control is intentionally icon-only with an accessible label so it does not compete with Markdown content, headings, or the existing top "展开全文" action.
