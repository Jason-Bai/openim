# REQ-0031 Implementation Plan

## Scope

Implement the approved width and copy behavior in the web chat UI only.

## Steps

1. Update `MessageRenderer` so non-user rich/text messages render a copy button that writes `message.content` to the clipboard.
2. Update chat message CSS so non-user bubbles stretch to the available message row width while user bubbles keep their compact alignment.
3. Preserve existing long-message collapse and rich content rendering.
4. Run web tests and production build.

## Verification

- `npm run test -w apps/web`
- `npm run build -w apps/web`
