# Beta-0 接入闭环目标与 TODO

> Last updated: 2026-07-04
>
> Status: active product focus.
>
> This page is the current working dashboard for OpenIM. Keep it short enough to scan before starting work.

---

## Current Product Positioning

OpenIM should not be treated as a full IM product yet.

Current positioning:

> Internal employee entry point for connecting, chatting with, and diagnosing OpenClaw assistants.

The core value is this path:

```text
员工账号
  -> 默认 BOT
  -> OpenClaw 助手槽位
  -> Plugin / Gateway
  -> 可聊天会话
  -> 可诊断、可恢复
```

Do not optimize for Slack/Feishu replacement features until this path is simple and reliable.

---

## Beta-0 Goal

Beta-0 has one goal:

> A real internal employee can connect their own OpenClaw assistant without reading the README, confirm it is online and usable, and recover or diagnose common failures.

This means Beta-0 is not just "the APIs exist". The flow must be understandable from the product surface.

---

## Current Stage

Product maturity:

```text
Internal Alpha late stage -> Beta-0 preparation
```

Already in place:

- Register / login.
- Default BOT.
- `/new-bot` and `/connect`.
- BOT Gateway / Plugin connection path.
- Conversation and message persistence basics.
- Employee friendship approval and direct chat.
- Smoke and regression scripts.
- Recent reliability and UI fixes from loop work.

Main gaps:

- First-time OpenClaw assistant onboarding is still too command/manual driven.
- Connection status copy is too technical and does not always tell the user what to do next.
- Release docs, README, P0/P1 docs, and implemented behavior need a clean alignment pass.
- No single Beta-0 acceptance baseline exists yet.
- No real 3-5 person internal trial data exists yet.

---

## Priority TODOs

### P0 - Beta-0 Must Have

- [ ] Build a first-time "Connect OpenClaw Assistant" guided flow.
  - Include create slot, get connection info, copy config, start plugin, detect online state, and send test message.
- [ ] Define the Beta-0 acceptance baseline.
  - Include required smoke commands, E2E coverage, release note state, known issues, and go/no-go criteria.
- [ ] Productize connection diagnostics.
  - Distinguish token error, BOT not started, heartbeat timeout, duplicate connection, gateway unavailable, and plugin not connected.
  - Every failure state should show a next action.
- [ ] Add or update full happy-path E2E.
  - New user registration -> default BOT -> create/connect OpenClaw BOT -> plugin online -> message exchange -> reload preserves history.
- [ ] Align docs with current implementation.
  - README, release notes, P0/P1 scope docs, and workflow docs should describe the same product state.

### P1 - Beta-0 Trial Readiness

- [ ] Run a 3-5 person internal trial.
  - Track where users get stuck, what copy they misunderstand, and which recovery paths fail.
- [ ] Add a lightweight trial feedback template.
  - Capture setup time, failure reason, whether users could recover, and first successful message time.
- [ ] Add a support/debug checklist for operators.
  - Include where to inspect gateway logs, bot state, token status, and message delivery.

### Not Now

- [ ] Group chat.
- [ ] File upload.
- [ ] Organization directory/admin console.
- [ ] Complex permissions or anti-spam.
- [ ] Full mobile IM redesign.
- [ ] Public npm publishing or complex plugin distribution.

---

## Agent Routing

Use the agent team like this:

| Phase | Agent | Output |
|---|---|---|
| Product scope | `product-manager` | PRD, scope, acceptance criteria, priority calls |
| Technical plan after scope is approved | `architect` | Technical design and implementation plan |
| UI flow and state design | `ui-designer` | UX/UI design doc and copy/state decisions |
| Frontend implementation | `frontend-developer` | UI and client behavior |
| Backend implementation | `backend-architect` | API, Gateway, schema, diagnostics |
| QA baseline | `tester` | E2E/smoke plan and test report |
| Delivery check | `reviewer` | Risk review before merge/release |
| Deployment/release | `deployer` | Deployment notes, environment checks, rollback |

---

## Acceptance Criteria

Beta-0 can be considered ready for internal trial only when:

- A new employee can complete the first-time connect flow from the UI without reading developer docs.
- The connected assistant appears online in the expected conversation/contact surfaces.
- The user can send a test message and see a persisted conversation after reload.
- The most common connection failures display user-actionable recovery instructions.
- Required smoke/E2E commands are documented and passing.
- Release notes and known issues are current.
- The team can explain current scope, non-goals, and next TODOs from this page.

---

## Related Docs

- `docs/overall-plan.md` - original system plan and stage definitions.
- `docs/tasks.md` - detailed historical task breakdown.
- `docs/workflow.md` - product development workflow.
- `docs/product/README.md` - product document conventions.
- `docs/plugin-npm-package.md` - plugin package plan.
