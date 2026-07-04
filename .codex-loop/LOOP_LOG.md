# Loop Log

## Round 1 - Preserve Code Message Content Type

- Discover: Static inspection found `content_type: "code"` is accepted but user
  messages are persisted with hard-coded `"text"`.
- Plan: Add failing backend regression test, then thread validated content type
  through send helpers.
- Execute: Added failing regression test, confirmed RED (`content_type` was
  `text`), then threaded validated `content_type` through backend send helpers.
- Verify: Pass. Targeted regression passed after fix; full backend P0 passed
  with 36 tests; web test and web build passed.
- Checker: PASS. Scope is limited to `.codex-loop/`, one backend regression
  test, and the message service content-type threading fix. Risk is low.
- Result: Loop round completed successfully.
- Next: Wait for the next loop-managed task.

## Round 2 - Frontend Code Message Content Type

- Discover: Frontend send path hardcodes `content_type: "text"` and retry drops
  the previous message content type.
- Intake: Scope is limited to web API/client send path, retry path, and a
  one-off regression script because the web package has no runtime test runner.
- Plan: Write failing regression script, update send API to accept optional
  content type, thread content type through submit/retry, then run verification.
- Execute: Added one-off regression script, confirmed RED, then updated
  `sendConversationMessage`, optimistic payloads, and retry to preserve content
  type.
- Verify: Pass. Regression script passed; backend P0 passed with 36 tests; web
  test and build passed.
- Checker: PASS. Scope is limited to frontend send/retry path, regression
  script, and project loop state files.
- Self-Evolution Audit:
  - Proactively Discovered: project-local `.codex-loop` lacked newer
    `INTAKE.md` and `PROBES.md` files.
  - User-Corrected: OpenIM had `.superpowers/` artifacts, but this loop did
    not inspect or use them during Intake.
  - Evolution Candidates: root `evo-004-project-loop-schema-propagation`
    promoted; root `evo-006-resource-route-evidence` promoted.
- Result: Loop round completed successfully.
- Next: Wait for the next loop-managed task.

## Round 3 - Contacts Panel AI Deduplication

- Discover: `.superpowers/brainstorm/9999-1779846793/contact-ia-options.html`
  identifies duplicated AI entries across two contact groups as the biggest
  contacts IA issue. Static inspection confirmed `ContactsPanel` renders `ai`
  and then renders `all`, where `all` can include both AI and users.
- Intake: Scope is limited to the web contacts panel grouping and a one-off
  regression script. Backend contact API and broader IA redesign are out of
  scope.
- Capability Fit:
  - Discover used `.superpowers` plus static code search.
  - Execute uses TDD and React display-state guidance.
  - Browser automation is considered but not required unless command
    verification leaves ambiguity.
- Plan: Add a failing regression script, filter the second contact list to
  employees, rename the label to `员工联系人`, then run project verification.
- Execute: Added a one-off regression script and confirmed RED before fixing:
  the panel lacked an employee-only list, still used the `全部联系人` label, and
  rendered the second list from `all`.
- Verify: Pass. `node scripts/test-web-contact-panel-dedup.mjs`,
  `node scripts/test-web-code-message-payload.mjs`,
  `npm run test -w apps/web`, and `npm run build -w apps/web` all exited 0.
- Checker: PASS. The task-specific diff is limited to `ContactsPanel`, a
  regression script, and loop state. Existing dirty files from earlier loop
  tasks remain unrelated.
- Self-Evolution Audit:
  - Proactively Discovered: Capability Fit was required, but `AGENTS.md` and
    the Project Loop Schema did not require `CAPABILITIES.md`.
  - User-Corrected: None in this loop.
  - Evolution Candidates: root `evo-008-capability-schema-propagation` promoted
    and `CAPABILITIES.md` propagated into OpenIM `.codex-loop/`.
- Result: Loop round completed successfully.
- Next: Wait for the next loop-managed task.

## Round 4 - Default BOT Command Contact Refresh

- Discover: QA report recorded P1 `/new-bot` does not refresh contacts
  immediately. The IA/stability spec requires refreshing `contacts` and
  `conversations` after successful default BOT commands that can change BOT
  state. Static inspection showed the send success path merged messages and
  invalidated conversations, but did not invalidate contacts.
- Intake: Scope is limited to frontend cache invalidation after successful
  default BOT state-changing commands and a one-off regression script. Backend
  command metadata, optimistic contact insertion, and loading/error redesign are
  out of scope.
- Capability Fit:
  - Discover used QA docs, `.superpowers`, and static search.
  - Execute used TDD and React query-cache guidance.
  - Browser automation was considered but skipped because this narrow behavior
    is directly verified by command-level regression and TypeScript build.
- Plan: Add a failing regression script for default BOT command refresh, add a
  minimal command classifier, invalidate contacts after matching successful
  sends, then run project verification.
- Execute: Added `scripts/test-web-default-bot-command-refresh.mjs`, confirmed
  RED, then added `shouldRefreshDefaultBotState` and contacts invalidation in
  the send success path.
- Verify: Pass. `node scripts/test-web-default-bot-command-refresh.mjs`,
  `node scripts/test-web-code-message-payload.mjs`,
  `node scripts/test-web-contact-panel-dedup.mjs`,
  `npm run test -w apps/web`, and `npm run build -w apps/web` all exited 0.
  Vite reported the existing chunk-size warning during build.
- Checker: PASS. The task-specific diff is limited to the frontend send success
  path, one regression script, and loop records.
- Self-Evolution Audit:
  - Proactively Discovered: two local OpenIM paths exist; the active loop state
    is under `/Users/baiyu/.openclaw/workspace/projects/openim`.
  - User-Corrected: None in this loop.
  - Evolution Candidates: None; existing delivery notes already cover
    control-plane/worktree alignment.
- Result: Loop round completed successfully.
- Next: Wait for the next loop-managed task.
