# Loop State

## Current Task

None.

## Current Phase

idle

## Current Branch

main

## Iteration Count

1

## Max Iterations

3

## Last Action

Completed the frontend default BOT command refresh loop.

## Last Verification

Pass:

- `node scripts/test-web-default-bot-command-refresh.mjs`: pass
- `node scripts/test-web-contact-panel-dedup.mjs`: pass
- `node scripts/test-web-code-message-payload.mjs`: pass
- `npm run test -w apps/web`: pass (`tsc -b --noEmit`)
- `npm run build -w apps/web`: pass (`vite build`; existing chunk-size warning)

## Last Failure

Expected RED before fix:

- `node scripts/test-web-default-bot-command-refresh.mjs`: failed because
  `App.tsx` had no default BOT state-command classifier and did not invalidate
  `contacts` after successful state-changing default BOT commands.

## Next Step

Wait for the next loop-managed task.

## Problem Intake

- Problem: After sending `/new-bot`, the new OpenClaw BOT was created but did
  not appear in Contacts until another mutation or page refresh.
- Evidence:
  - `docs/tests/2026-05-27-ui-ux-qa-optimization-report.md` records P1:
    `/new-bot` does not refresh contacts immediately.
  - `docs/superpowers/specs/2026-05-27-ui-ux-information-architecture-stability-design.md`
    requires invalidating/refetching `contacts` and `conversations` after
    successful default BOT commands that change BOT state.
  - Static inspection showed the send success path updated messages and
    conversations, but did not refresh contacts for default BOT commands.
- In Scope:
  - `apps/web/src/pages/App.tsx`
  - `scripts/test-web-default-bot-command-refresh.mjs`
  - `.codex-loop/` task state and verification records
- Out Of Scope:
  - Backend default BOT command response metadata
  - Optimistic contact insertion
  - Browser-visible loading/error state redesign
  - Unrelated dirty files from earlier loop runs
- Success Criteria:
  - Regression script fails before the fix and passes after the fix.
  - Successful state-changing default BOT commands invalidate `contacts`.
  - The send path continues to invalidate `conversations`.
  - `npm run test -w apps/web` and `npm run build -w apps/web` pass.
- Risks: Low; change is limited to frontend cache invalidation after successful
  sends.
- Rollback Plan:
  - Remove the default BOT command classifier, contacts invalidation, and the
    regression script.

## Resource Route Evidence

- `.superpowers/` checked: yes.
- `.superpowers` artifact used:
  `.superpowers/brainstorm/9999-1779846793/ui-ux-prd-scope.html`.
- Project docs used:
  `docs/tests/2026-05-27-ui-ux-qa-optimization-report.md` and
  `docs/superpowers/specs/2026-05-27-ui-ux-information-architecture-stability-design.md`.
- Skills used:
  - `systematic-debugging` for bug framing.
  - `test-driven-development` for red/green regression.
  - `frontend-react-best-practices` for minimal React query-cache changes.
- Skills considered:
  - `browser-automation`: useful for visual smoke, skipped because command-level
    regression and TypeScript build directly verify this cache-invalidation
    rule.
  - `ui-ux-pro-max`: considered, skipped because the `.superpowers` artifact
    and QA report already define the behavior.

## Capability Fit

- Phase: Discover
- Candidate capabilities: project `.superpowers/`, project docs, `rg`, project loop state.
- Used: QA report, IA/stability spec, `.superpowers` scope artifact, and
  static code search.
- Skipped with reason: GitHub / CI tools were skipped because the task is a
  local frontend cache behavior bug sourced from project docs.
- Missing capability / follow-up: None.

- Phase: Execute
- Candidate capabilities: `acpx codex`, TDD script, React best practices.
- Used: local TDD script and React best-practice review.
- Skipped with reason: `acpx codex` was skipped for this small in-session fix;
  the project loop still records Maker-style execution and verification.
- Missing capability / follow-up: Consider adding an executable project helper
  that wraps `acpx codex` for future larger Maker delegations.

## Checker Review

- Verdict: PASS
- Main Issues: None.
- Risk Level: Low
- Required Fixes: None.
- Suggested PR Summary: Refresh contacts after successful state-changing
  default BOT commands so newly created or changed BOTs appear without a page
  reload.

## Self-Evolution Audit

### Proactively Discovered

- The project has two local OpenIM paths; only
  `/Users/baiyu/.openclaw/workspace/projects/openim` contains the active
  project-local `.codex-loop/`. This should be kept visible in handoffs to
  avoid splitting loop state across directories.

### User-Corrected

- None in this loop.

### Evolution Candidates

- None. The two-path observation is already covered by existing delivery
  control-plane notes about aligning control-plane and worktree location.

## PR Summary

### Summary

This PR fixes the default BOT command refresh gap where newly created or
changed BOTs did not appear in Contacts until another refresh path ran.

### Changes

- Added a default BOT state-command classifier for `/new-bot`, `/delete-bot`,
  `/connect`, `/disconnect`, and `/diagnose`.
- Invalidated `contacts` after successful matching default BOT sends.
- Added a one-off regression script for the command-refresh rule.
- Updated Loop state, queue, verification, and capability evidence.

### Verification

- `node scripts/test-web-default-bot-command-refresh.mjs`: pass
- `node scripts/test-web-contact-panel-dedup.mjs`: pass
- `node scripts/test-web-code-message-payload.mjs`: pass
- `npm run test -w apps/web`: pass
- `npm run build -w apps/web`: pass

### Risk

Risk level: Low.

### Notes

`npm run build -w apps/web` still reports the existing Vite chunk-size warning;
the build exits 0.
