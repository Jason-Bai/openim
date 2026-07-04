# Self-Evolution Report: openim-workspace-mvp

date: 2026-07-01
release: openim-workspace-mvp
work_item: openim-workspace-mvp-release-polish

## 主动发现

### 1. Mobile and desktop browser smoke found a layout issue

observation: The left rail logout button overflowed the 56px navigation rail in browser screenshots.
action: Changed the logout control to an icon-only button with `aria-label="退出"`.
verification: Re-ran build/test, desktop browser smoke, mobile browser smoke, and a DOM containment check.
evolution_link: This should remain part of release polish browser smoke.

### 2. Ledger audit found a wrong registry target

observation: A broad patch updated the `baseline` worktree status instead of `release-polish`.
action: Corrected `.codex/delivery/worktrees.md` and added `evo-002-ledger-target-verification`.
verification: Re-read the intended `release-polish` entry and adjacent registry entries after correction.
evolution_link: OpenIM constraints now require checking the intended ledger entry and an adjacent entry after registry edits.

## 用户指出

### 1. MVP scope was too broad for one work item

observation: The user pointed out that the MVP could and should be decomposed.
action: Created release slices and marked `loop-mvp` as prototype only.
verification: `openim-workspace-mvp` release ledger now has baseline, login-shell, chat-layout, task-static, app-center, and release-polish slices.
evolution_link: `evo-001-active-self-evolution`.

### 2. Screenshot artifacts were not discoverable from the target project

observation: The user pointed out that screenshots were only in the worktree-local `.codex` path.
action: Mirrored screenshots to `/Users/baiyu/workspaces/gitlab/openim/.codex/delivery/artifacts/openim-workspace-mvp-release-polish/screenshots`.
verification: The project-level artifact path contains login, tasks, apps, and mobile-tasks screenshots.
evolution_link: `evo-003-project-level-artifact-index`.

### 3. Self-evolution was not visible enough

observation: The user pointed out that self-evolution was not visible in the handoff.
action: Added a system rule requiring every major handoff to include a `Self-Evolution Report` with separate `主动发现` and `用户指出` sections.
verification: `tests/validate_self_evolution.sh` now checks for the report and labels.
evolution_link: This report is the first explicit application of that rule.

## Current Assessment

The OpenIM MVP has some actual proactive findings, but the largest process improvements were user-triggered. That means the system improved, but the previous handoff overstated the visibility of self-evolution. Future handoffs must expose this distinction explicitly.
