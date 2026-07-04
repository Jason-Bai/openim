# Evolution Ledger

Loop: observe -> reflect -> hypothesize -> correct -> revalidate -> probe -> promote-or-reopen

## Evolution Candidates

- id: evo-001-active-self-evolution
  date: 2026-06-30
  source: user correction during OpenIM Workspace MVP planning
  signal: self-review-finding
  observation: The orchestrator initially reacted to a specific MVP decomposition issue instead of proactively recognizing that Loop Engineering itself must actively evolve.
  reflection: A delivery supervisor that waits for the user to identify process gaps is not self-evolving; it needs a dedicated ledger and loop for process improvement.
  hypothesis: If every process correction creates a candidate with correction, revalidation, next_probe, and close_condition, the system will actively detect recurrence instead of only recording lessons.
  generalized_rule: User corrections, repeated failures, prototype spike findings, missing verification, weak decomposition, and unsafe sequencing must create evolution candidates.
  correction: Added self-evolution reference, target evolution ledger, validation tests, and explicit handoff report requirements.
  encoded_in: codex-delivery-system self-evolution reference, target evolution ledger, validation tests
  verification: scripts/validate.sh in codex-delivery-system
  revalidation: tests/validate_self_evolution.sh checks self-evolution terms and report visibility; scripts/validate.sh passed after encoding.
  next_probe: At the next OpenIM delivery handoff, inspect whether self-evolution report separates proactive discoveries from user-corrected findings and whether new candidates have revalidation fields.
  close_condition: Candidate remains promoted only if the next major handoff includes a complete Self-Evolution Report and no promoted candidate lacks revalidation.
  promotion_target: delivery-orchestrator skill, self-evolution reference, OpenIM delivery constraints and decisions
  status: promoted

- id: evo-002-ledger-target-verification
  date: 2026-07-01
  source: release-polish registry update
  signal: self-review-finding
  observation: A broad ledger patch updated the baseline worktree status instead of the release-polish worktree status.
  reflection: Delivery ledgers are executable project memory; an incorrect status can misroute later work even when code is correct.
  hypothesis: If every registry edit is followed by targeted entry inspection plus adjacent-entry inspection, mistaken broad patches will be caught before handoff.
  generalized_rule: After editing project-level registries, verify the intended target entry and at least one adjacent entry.
  correction: Corrected release-polish registry status and added the registry-inspection constraint.
  encoded_in: OpenIM delivery constraints
  verification: inspected `.codex/delivery/worktrees.md` after correction and confirmed release-polish owns `ready-for-review`
  revalidation: Re-read `.codex/delivery/worktrees.md` and confirmed baseline is not-ready while release-polish is ready-for-review.
  next_probe: Before the next registry update handoff, run `sed -n` over the full target registry and confirm the intended entry plus adjacent entries.
  close_condition: Candidate stays promoted only if future registry edits include explicit target-entry evidence in the handoff.
  promotion_target: `.codex/delivery/constraints.md`
  status: promoted

- id: evo-003-project-level-artifact-index
  date: 2026-07-01
  source: user correction about screenshot location
  signal: self-review-finding
  observation: Browser smoke screenshots were stored only inside the release-polish worktree, making them less discoverable from the OpenIM project control plane.
  reflection: Worktree-local evidence is useful for a task, but release evidence also needs a project-level index or mirror.
  hypothesis: If release-gate artifacts are mirrored or indexed from the project control plane, reviewers can discover evidence without knowing the active worktree path.
  generalized_rule: Verification artifacts for release gates must be referenced or mirrored from the target project's `.codex/delivery` control plane.
  correction: Mirrored screenshots to the OpenIM project-level delivery artifacts directory and added the artifact-index constraint.
  encoded_in: OpenIM release notes and artifact mirror
  verification: screenshots copied to `.codex/delivery/artifacts/openim-workspace-mvp-release-polish/screenshots`
  revalidation: Listed the project-level screenshots directory and confirmed login, tasks, apps, and mobile-tasks images exist.
  next_probe: At the next browser smoke, check that every screenshot path appears either in `.codex/delivery/artifacts` or in the release notes before final handoff.
  close_condition: Candidate remains promoted only if release screenshots are discoverable from the target project control plane.
  promotion_target: `.codex/delivery/releases.md`
  status: promoted

- id: evo-004-visible-self-evolution-report
  date: 2026-07-01
  source: user correction about invisible self-evolution
  signal: self-review-finding
  observation: Self-evolution events existed in ledgers, but the handoff did not clearly separate proactive findings from user-corrected findings.
  reflection: Hidden ledger updates do not demonstrate active self-evolution to the user or future supervisor sessions.
  hypothesis: If every major handoff contains a visible Self-Evolution Report with `主动发现` and `用户指出`, the user can judge whether the system actually found issues proactively.
  generalized_rule: Every release or major handoff must include a Self-Evolution Report with `主动发现` and `用户指出` sections.
  correction: Added the OpenIM Self-Evolution Report and updated delivery-orchestrator validation to require report labels.
  encoded_in: codex-delivery-system self-evolution rules, validation test, OpenIM self-evolution report
  verification: `tests/validate_self_evolution.sh` requires `Self-Evolution Report`, `主动发现`, and `用户指出`
  revalidation: `scripts/validate.sh` passed after the report requirement was encoded.
  next_probe: At the next final answer for a release or major handoff, include a Self-Evolution Report summary and check whether proactive findings are actually proactive.
  close_condition: Candidate remains promoted only if future major handoffs expose the distinction without user prompting.
  promotion_target: delivery-orchestrator skill and OpenIM delivery report
  status: promoted

- id: evo-005-release-registry-section-scope
  date: 2026-07-01
  source: openim-loop-mvp release creation
  signal: tool-failure
  observation: Creating the new release exposed that `create-release.sh` could corrupt `worktrees.md` when writing `depends_on` for a dependent slice; fields after `depends_on` were swallowed.
  reflection: A loop control script that mutates project memory must be section-scoped and covered by regression tests, otherwise the control plane can drift even when code implementation succeeds.
  hypothesis: If release script edits are constrained to the current worktree section and smoke tests assert downstream fields remain present, dependency writes will not corrupt adjacent registry content.
  generalized_rule: Registry mutation tools must update only the intended section and must have smoke coverage for dependent slices preserving `merge_status`.
  correction: Fixed `skills/delivery-orchestrator/scripts/create-release.sh` section-scoped dependency replacement and added smoke assertions in `tests/smoke_loop_engineering.sh`.
  encoded_in: codex-delivery-system create-release script and smoke test
  verification: `bash scripts/validate.sh` in `/Users/baiyu/workspaces/laboratory/codex-delivery-system` passed after the fix.
  revalidation: Recreated OpenIM control-plane `worktrees.md` with complete sections for `openim-loop-mvp-*` and no stale `openim-workspace-mvp-*` entries.
  next_probe: On the next release creation with dependent slices, inspect each dependent worktree section and confirm `depends_on`, `conflicts_with`, `affected_files`, `merge_status`, and `last_sync` remain present.
  close_condition: Candidate remains promoted only if future dependent slice creation preserves the full worktree section.
  promotion_target: codex-delivery-system scripts and smoke tests
  status: promoted

- id: evo-006-project-local-worktree-root
  date: 2026-07-01
  source: user correction after openim-loop-mvp worktree creation
  signal: user-correction
  observation: The orchestrator created OpenIM worktrees under the parent workspace `.worktrees` directory even though the project rule is to create them under the target project's own `.worktrees` directory.
  reflection: The control-plane location and worktree location must be aligned; otherwise project-level context is split across directories and the supervisor violates the target workspace boundary.
  hypothesis: If create-work-item/create-release use `<target-project>/.worktrees/<work-item-id>` and automatically ignore `.worktrees/`, future target projects will keep all delivery worktrees inside their own workspace without polluting git status.
  generalized_rule: Delivery worktrees belong under `<target-project>/.worktrees`, not under the target project's parent directory.
  correction: Moved OpenIM delivery worktrees into `/Users/baiyu/workspaces/gitlab/openim/.worktrees`, added `.worktrees/` to OpenIM `.gitignore`, updated codex-delivery-system scripts/docs/tests to use project-local worktrees, and added smoke coverage for the ignore rule.
  encoded_in: codex-delivery-system create-work-item/create-release scripts, context docs, orchestrator skill, smoke tests, OpenIM `.gitignore`
  verification: `bash scripts/validate.sh` in `/Users/baiyu/workspaces/laboratory/codex-delivery-system` passed after the path change.
  revalidation: `git worktree list` for OpenIM now shows `loop-mvp` and `openim-loop-mvp-*` under `/Users/baiyu/workspaces/gitlab/openim/.worktrees`.
  next_probe: On the next target-project worktree creation, inspect `git worktree list` and assert the worktree path starts with `<target-project>/.worktrees/`.
  close_condition: Candidate remains promoted only if no new delivery worktree for OpenIM or a future target project is created under the parent workspace `.worktrees`.
  promotion_target: codex-delivery-system scripts, docs, smoke tests, and OpenIM delivery ledger
  status: promoted
