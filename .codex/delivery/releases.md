# Release Registry

## openim-workspace-mvp

status: superseded
target_project: /Users/baiyu/workspaces/gitlab/openim
release_goal: Publish a front-end Workspace MVP on top of the existing OpenIM app without backend scope expansion.
release_gate: superseded
standard_verification:
merge_order:
active_loop: release-loop
loop_signal: user-correction
feedback_queue:
next_action: Superseded by `openim-loop-mvp`; implementation worktrees were deleted on 2026-07-01 at user request.
learning_log:
- source: loop-mvp prototype
  lesson: Static tasks and app center can be separate MVP slices after the workspace shell exists.

release_notes:
- Old implementation worktrees were deleted.
- Replacement release: `openim-loop-mvp`.

## openim-loop-mvp

status: candidate
target_project: /Users/baiyu/workspaces/gitlab/openim
release_goal: Publish a front-end OpenIM Workspace MVP using the new Loop Engineering control-plane flow.
release_gate: `npm run build -w apps/web`, `npm run test -w apps/web`, and browser smoke for workspace shell, tasks, apps, and mobile tasks pass.
standard_verification: npm run build -w apps/web; npm run test -w apps/web; browser smoke
merge_order: baseline -> workspace-vertical-slice -> release-verification
active_loop: release-loop
loop_signal: user-correction
feedback_queue:
next_action: Review and merge `/Users/baiyu/workspaces/gitlab/openim/.worktrees/openim-loop-mvp-workspace-vertical-slice` after final human review.
learning_log:
- source_work_item: openim-loop-mvp-workspace-vertical-slice
  signal: user-correction
  lesson: Re-implementation should use a new release id, delete stale implementation worktrees, and keep a single project control plane as source of truth.
  policy_update: Use `Signal -> Context -> Policy -> Action -> Verification -> Promotion` before claiming MVP readiness.
  verification_update: Record screenshots and smoke summary in worktree and project-level artifacts.
  applies_to: OpenIM MVP delivery

### Slices

#### baseline

work_item: openim-loop-mvp-baseline
status: complete
goal: Re-establish the baseline after deleting old MVP implementation worktrees.
scope: Keep target project control plane, remove stale worktree registry entries, and confirm commands.
non_goals: No product UI change.
depends_on: 
acceptance_gate: Old `openim-workspace-mvp-*` worktrees are absent from the git worktree list.
verification_commands: git worktree list
worktree: /Users/baiyu/workspaces/gitlab/openim/.worktrees/openim-loop-mvp-baseline
release_notes:
- Old implementation worktrees named `openim-workspace-mvp-*` were removed.

#### workspace-vertical-slice

work_item: openim-loop-mvp-workspace-vertical-slice
status: ready-for-review
goal: Implement the minimum publishable front-end workspace MVP in one coherent vertical slice.
scope: Workspace icon rail, authenticated shell, existing chat/contact surfaces, static task center, static app center, settings placeholder, responsive polish.
non_goals: No backend task API, no real app marketplace install flow, no auth/chat API contract changes.
depends_on: baseline
acceptance_gate: Build/test pass and browser smoke confirms shell, tasks, apps, and mobile task layout.
verification_commands: npm run build -w apps/web; npm run test -w apps/web; browser smoke
worktree: /Users/baiyu/workspaces/gitlab/openim/.worktrees/openim-loop-mvp-workspace-vertical-slice
release_notes:
- Implemented in `apps/web/src/pages/App.tsx` and `apps/web/src/styles.css`.
- Browser smoke screenshots: `/Users/baiyu/workspaces/gitlab/openim/.codex/delivery/artifacts/openim-loop-mvp-workspace-vertical-slice/screenshots`.

#### release-verification

work_item: openim-loop-mvp-release-verification
status: pending
goal: Final human review, merge readiness, and optional full-stack smoke.
scope: Review diff, confirm project artifacts, decide whether full-stack backend smoke is required before merge.
non_goals: New product scope.
depends_on: workspace-vertical-slice
acceptance_gate: Human review accepts candidate and remaining risk is recorded.
verification_commands: npm run build -w apps/web; npm run test -w apps/web; browser smoke; optional backend-backed chat smoke
worktree: /Users/baiyu/workspaces/gitlab/openim/.worktrees/openim-loop-mvp-release-verification
release_notes:
