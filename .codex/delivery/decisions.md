# Decisions

## OpenIM Workspace MVP Decomposition

decision: The `loop-mvp` worktree is a prototype spike only. It must not be treated as the release branch.
reason: The MVP contains multiple independently verifiable slices: baseline, login shell, chat layout, static tasks, static app center, and release polish.
impact: Release work must proceed through `openim-workspace-mvp` slices recorded in `releases.md`.

## Supervisor Self-Review

decision: Before creating implementation worktrees for broad goals, run `supervisor-self-review` and scope pressure test.
reason: The orchestrator should detect over-broad MVP scope before the user has to point it out.
impact: Broad work enters `decomposition-loop` with `loop_signal: release-too-broad`.
