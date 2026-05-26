# AGENTS.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

---

## 5. Project Context

This repository is `openim`: an IM prototype for employee accounts, default BOT onboarding, OpenClaw employee-assistant BOT integration, and employee-to-employee chat.

Architecture reference: [docs/architecture.md](docs/architecture.md).

Primary modules:

- `apps/server`: FastAPI backend. Owns auth, users, friendships, bots, conversations, messages, employee WebSocket, and BOT Gateway.
- `apps/web`: React + Vite frontend. Owns contacts, conversations, profiles, and chat UI.
- `packages/openclaw-bot-plugin`: npm package for external/OpenClaw BOTs to connect to OpenIM.
- `scripts/openclaw-local-bridge.mjs`: local bridge from an OpenIM BOT slot to the local OpenClaw agent.
- `docs`: product, backend, frontend, plugin, task, and architecture plans.

Current P0 rule:

- Default BOT, OpenClaw employee-assistant BOT, and human employee chat should use the unified `conversations/messages` model.
- Conversation lists and message history must be backend-backed so refresh does not lose state.
- Local-only UI state is acceptable only for short-lived optimistic sending.

Development defaults:

- Backend: `http://127.0.0.1:8080`
- Frontend: `http://127.0.0.1:5173`
- Dev DB: `apps/server/openim.db`
- Plugin package: `@openim/openclaw-bot-plugin`

Common verification:

- Backend tests: `cd apps/server && uv run pytest -q`
- Backend lint: `cd apps/server && uv run ruff check .`
- Frontend type check: `npm run test -w apps/web`
- Frontend build: `npm run build -w apps/web`
