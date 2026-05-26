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
8. Implement only the approved scope in the dedicated branch/worktree.
9. Run relevant verification commands and update test/deployment evidence.
10. Open a PR with linked Issue, registry, docs, verification evidence, risks, and rollback notes.
