# Verification Guide

OpenIM is a mixed workspace:

- `apps/server`: FastAPI / SQLAlchemy backend managed with `uv`.
- `apps/web`: React / TypeScript / Vite web app.
- `packages/openclaw-bot-plugin`: TypeScript OpenClaw BOT Gateway plugin.
- `scripts/`: local regression and end-to-end smoke scripts.

Use the smallest command set that objectively covers the active loop task. Do
not keep old task-specific scripts in the required path unless the current
change touches that behavior.

## Always

Run a targeted regression first when the task has a specific bug, API contract,
or UI behavior. Add one if no existing command can fail for the bug.

Only report a command as passing if it was run fresh in this worktree and exited
successfully.

## Backend Changes

Use when files under `apps/server/` change, or when the task affects API,
message persistence, auth, conversations, contacts, friends, websockets, bot
gateway behavior, database schema, or backend docs.

```bash
cd apps/server && uv run pytest -q
cd apps/server && uv run ruff check .
```

For narrow backend fixes, run the focused pytest node first, then the full
backend suite before completion.

Example:

```bash
cd apps/server && uv run pytest tests/test_p0_flow.py::test_name_here -q
cd apps/server && uv run pytest -q
```

## Web Changes

Use when files under `apps/web/` change, or when the task affects browser UI,
frontend API payloads, contact/message rendering, React state, TypeScript types,
or Vite build output.

```bash
npm run test -w apps/web
npm run build -w apps/web
```

Current optional web regression scripts:

```bash
node scripts/test-web-default-bot-command-refresh.mjs
node scripts/test-web-code-message-payload.mjs
node scripts/test-web-contact-panel-dedup.mjs
```

Run these only when the active task touches default BOT command cache refresh,
code-message payload preservation, or contacts-panel AI/user grouping.

## Plugin Changes

Use when files under `packages/openclaw-bot-plugin/` change, or when the task
affects OpenClaw BOT Gateway packaging, types, or plugin runtime behavior.

```bash
npm run test -w packages/openclaw-bot-plugin
npm run build -w packages/openclaw-bot-plugin
```

## Cross-Cutting Changes

Use when changes span multiple packages, shared contracts, workspace scripts,
lockfiles, or project-wide docs that describe verified behavior.

```bash
npm run test
npm run build
cd apps/server && uv run pytest -q
cd apps/server && uv run ruff check .
```

If the change affects browser-to-backend flows, also run the relevant smoke
script:

```bash
npm run e2e:p0
npm run e2e:p0:plugin
npm run e2e:p05
npm run e2e:openclaw:local
```

Pick the smoke command that matches the flow under test; do not run every e2e
script by default unless the task changes shared startup, protocol, or
end-to-end integration behavior.

## Docs / Loop-Only Changes

For `.codex-loop/`, docs, prompts, or process-only edits, verify the referenced
commands still match the project manifests and docs:

```bash
npm run test --workspaces --if-present
npm run build --workspaces
cd apps/server && uv run pytest -q
cd apps/server && uv run ruff check .
```

When the edit is only a command inventory or process correction, static
verification against `package.json`, `apps/*/package.json`,
`apps/server/pyproject.toml`, and `README.md` is acceptable if running the whole
suite would be unrelated.
