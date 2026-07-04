# Constraints

## Release Scope

- Do not merge `loop-mvp` as a release branch.
- Implement OpenIM Workspace MVP through the release slices in `.codex/delivery/releases.md`.
- `task-static` and `app-center` depend on `login-shell`, not on each other.
- `release-polish` depends on `chat-layout`, `task-static`, and `app-center`.

## Verification

- Run `npm run build -w apps/web` for each slice before marking it ready.
- Run `npm run test -w apps/web` for each slice before marking it ready.
- Use browser smoke checks for user-facing visual slices.
- After editing `.codex/delivery/worktrees.md` or `.codex/delivery/releases.md`, inspect the intended target entry and at least one adjacent entry before continuing.
- Mirror or index release-gate screenshots and other verification artifacts under the target project's `.codex/delivery` control plane, not only inside a worktree.
