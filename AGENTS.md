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

Project overview, module layout, local runbook, and document index live in [README.md](README.md). Treat README as the source of truth for project facts and update it instead of duplicating project information here.

Use [README.md](README.md), `package.json`, and package-level manifests for current local run and verification commands.

## 6. Product Workflow

Workflow reference: [docs/workflow.md](docs/workflow.md).

Default branch policy:

- Do not develop directly on `main`.
- Use one GitHub Issue per independently shippable feature, bug, or documentation workflow change.
- Use one dedicated branch and worktree per Issue.
- Keep `main` as the stable integration baseline.

Issue usage:

- Epic Issues track product stages or large initiatives.
- Feature Issues track independently shippable requirements.
- Bug Issues track incorrect existing behavior with reproduction and verification.
- Issues coordinate status and discussion; durable PRD, UX, technical design, implementation plan, and release notes live in `docs/`.

Branch naming:

- `feature/<issue-number>-short-name`
- `fix/<issue-number>-short-name`
- `docs/<issue-number>-short-name`
- `chore/<issue-number>-short-name`

Required gates for non-trivial work:

1. Confirm or create the GitHub Issue.
2. Create or update the delivery registry file under `docs/workflow/active/`.
3. Clarify product requirements and acceptance criteria.
4. Complete requirement review before technical design.
5. Write or update PRD/UX docs when the change affects product behavior or UI.
6. Write or update technical design and complete technical review before coding.
7. Write or update the implementation plan before coding.
8. Sync local `main` to `origin/main` with `git fetch origin --prune` and `git pull --ff-only origin main` before creating a worktree.
9. Implement only the approved scope in the dedicated branch/worktree created from updated `main`.
10. Run relevant verification commands and update test/deployment evidence.
11. Open a PR with linked Issue, registry, docs, verification evidence, risks, and rollback notes.

UI/UX analysis requests:

- When asked to analyze current UI problems, use the UI/UX design workflow before implementation.
- Output must include both critique and design direction: observed problem, user impact, priority, concrete UI change, affected surface, and verification method.
- Do not stop at a problem list. Provide an executable UI方案 with layout, hierarchy, states, accessibility, and responsive implications.
- If the user asks to implement the UI方案, then promote it into the normal Issue, registry, UX doc, technical design, implementation plan, branch/worktree, and verification flow above.


<!-- BEGIN CODEX DELIVERY SYSTEM -->
# AGENTS.md

## Goal

You are the coding agent for this project. Do not only write code. Complete the implementation, verification, repair, and summary loop.

## Loop Rule

For each task:

1. Read the relevant project context and `.codex/delivery` files.
2. Make a short plan.
3. Modify code.
4. Run the required validation commands.
5. If validation fails, read the error, update the feedback queue when appropriate, and continue repairing.
6. Repeat until validation passes or a stop condition is reached.
7. Final output must include changed files, core changes, validation commands, validation results, and remaining risk.

## Validation Commands

Prefer commands recorded in `.codex/delivery/constraints.md` and the active work item verification plan.

If no project-specific commands are recorded, inspect the project manifest first, then choose the closest equivalent of:

```bash
pnpm lint
pnpm test
pnpm build
```

## Stop Condition

Stop only when:

- Required validation passes.
- A product or technical decision needs human confirmation.
- The same blocking problem has failed three consecutive repair attempts.

## Delivery Context

Project-level context lives in:

```text
.codex/delivery/project.md
.codex/delivery/worktrees.md
.codex/delivery/decisions.md
.codex/delivery/constraints.md
```

Work-item context usually lives in the active Git worktree:

```text
.codex/delivery/work-item.md
.codex/delivery/plan.md
.codex/delivery/verification.md
```

Keep these files current when work spans turns or agents.


<!-- END CODEX DELIVERY SYSTEM -->
