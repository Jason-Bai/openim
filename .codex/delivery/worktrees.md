# Worktree Registry

## loop-mvp

path: /Users/baiyu/workspaces/gitlab/openim/.worktrees/loop-mvp
branch: feature/loop-mvp
base_branch: main
status: prototype
current_phase: intake
next_phase: requirements
owner: delivery-orchestrator
depends_on:
conflicts_with: openim-loop-mvp-*
affected_files:
merge_status: not-a-release-branch
last_sync:

## openim-loop-mvp-baseline

path: /Users/baiyu/workspaces/gitlab/openim/.worktrees/openim-loop-mvp-baseline
branch: feature/openim-loop-mvp-baseline
base_branch: main
release: openim-loop-mvp
slice: baseline
status: complete
current_phase: handoff
next_phase:
owner: delivery-orchestrator
depends_on:
conflicts_with:
affected_files:
merge_status: no-code-change
last_sync: 2026-07-01

## openim-loop-mvp-workspace-vertical-slice

path: /Users/baiyu/workspaces/gitlab/openim/.worktrees/openim-loop-mvp-workspace-vertical-slice
branch: feature/openim-loop-mvp-workspace-vertical-slice
base_branch: main
release: openim-loop-mvp
slice: workspace-vertical-slice
status: ready-for-review
current_phase: release-readiness
next_phase: merge-readiness
owner: delivery-orchestrator
depends_on: openim-loop-mvp-baseline
conflicts_with:
affected_files: apps/web/src/pages/App.tsx, apps/web/src/styles.css
merge_status: ready-for-review
last_sync: 2026-07-01

## openim-loop-mvp-release-verification

path: /Users/baiyu/workspaces/gitlab/openim/.worktrees/openim-loop-mvp-release-verification
branch: feature/openim-loop-mvp-release-verification
base_branch: main
release: openim-loop-mvp
slice: release-verification
status: pending
current_phase: release-readiness
next_phase: merge-readiness
owner: delivery-orchestrator
depends_on: openim-loop-mvp-workspace-vertical-slice
conflicts_with:
affected_files:
merge_status: waits-for-review
last_sync: 2026-07-01
