# OpenIM Product Development Workflow

> Status: active working agreement.
>
> This workflow keeps `main` stable, gives every change a clear product or bug entry point, and allows independent work to run in parallel without sharing a dirty workspace.

---

## 1. Source Of Truth

OpenIM uses three layers of source of truth:

GitHub repository:

```text
https://github.com/Jason-Bai/openim
```

| Layer | Purpose | Location |
|---|---|---|
| GitHub Issue | Work entry, status, discussion, ownership, links | GitHub Issues |
| Delivery registry | Current requirement phase, review status, branch/worktree, and linked artifacts | `docs/workflow/` |
| Repository docs | Durable PRD, UX design, technical design, implementation plan, release notes | `docs/` |
| Pull Request | Code review, CI, merge decision | GitHub Pull Requests |

Issues track and coordinate work. They do not replace durable docs for complex product, design, or technical decisions.

The delivery registry gives the project a global view of active work without forcing every branch to edit one large file. Each active requirement owns one YAML file under `docs/workflow/active/`.

---

## 2. Work Types

### Epic

Use an Epic Issue for a product stage or large initiative, such as `P1: employee-to-bot chat`.

An Epic Issue should link child Feature/Bug Issues and describe the stage goal, scope boundary, sequencing, and release target.

### Feature

Use a Feature Issue for one independently shippable product or engineering capability.

Feature work requires:

- Feature Issue.
- Registry file under `docs/workflow/active/`.
- PRD or scoped requirement doc for non-trivial product changes.
- UX design doc when UI behavior or layout changes.
- Technical design and implementation plan before coding.
- Dedicated branch and worktree.
- PR with verification evidence.

### Bug

Use a Bug Issue when existing behavior is wrong.

Bug work requires:

- Reproduction steps.
- Expected and actual behavior.
- Impact scope.
- Regression test or explicit verification command.
- Dedicated branch and worktree unless the fix is documentation-only and approved as trivial.

---

## 3. Required Flow

### 3.1 Requirement Registry

For non-trivial work, create a registry file before the requirement leaves the idea stage.

Use:

```text
docs/workflow/template.yml
```

and copy it to:

```text
docs/workflow/active/REQ-0000-short-name.yml
```

The registry file records:

- Current phase and status.
- GitHub Issue and PR.
- Branch and worktree.
- PRD, UX design, technical design, implementation plan, test report, and release note paths.
- Product, UX, technical, code, and QA review status.
- Deployment and smoke-test status.
- Blockers and dependencies.

Update the registry file whenever a gate changes. Parallel requirements should update separate registry files.

### 3.2 Product Requirement

Start with a GitHub Issue.

For non-trivial features, create a PRD under:

```text
docs/product/requirements/REQ-0000-short-name.md
```

The PRD should cover:

- Problem.
- Target users.
- Goal.
- Non-goals.
- Requirements.
- Acceptance criteria.
- Risks and open questions.

Set the registry `phase` to `requirement_review` while the PRD is under review. Move to `requirement_approved` only after product review approval.

### 3.3 UX/UI Design

If the work changes visible UI or user interaction, create a UX design doc under:

```text
docs/product/designs/REQ-0000-short-name.md
```

The UX design should cover:

- User flow.
- Page or component states.
- Empty, loading, error, and disabled states.
- Copy and interaction notes.
- Accessibility concerns.

Backend-only, protocol-only, or documentation-only work may skip this step.

Mark `reviews.ux_review` as `not_required` when this step is skipped.

### 3.4 Technical Design

Create a technical design under:

```text
docs/engineering/designs/REQ-0000-short-name.md
```

The design should cover:

- Architecture impact.
- Files/modules affected.
- API, schema, protocol, or state changes.
- Data flow.
- Error handling.
- Test strategy.
- Rollout and rollback notes when relevant.

Set the registry `phase` to `technical_review` while this design is under review. Move forward only after `reviews.technical_review: approved`.

### 3.5 Implementation Plan

Create an implementation plan under:

```text
docs/engineering/plans/REQ-0000-short-name.md
```

The plan should break work into small verifiable tasks. Each task should name files, tests, commands, and expected outcomes.

### 3.6 Branch And Worktree

Do not develop directly on `main`.

Before creating a branch or worktree, update the local `main` checkout to the latest remote stable baseline:

```bash
git fetch origin --prune
git switch main
git pull --ff-only origin main
```

If the local `main` worktree has unrelated uncommitted files, do not overwrite them. Either leave them untouched if they are untracked and unrelated, or stop and ask before proceeding.

Branch naming:

```text
feature/<issue-number>-short-name
fix/<issue-number>-short-name
docs/<issue-number>-short-name
chore/<issue-number>-short-name
```

Create the branch/worktree from the updated local `main`. Use one worktree per independent Issue. Parallel work should not share one checkout.

Record `branch.name` and `branch.worktree` in the registry file before development starts.

### 3.7 Development

Follow the approved plan. Keep changes surgical and scoped to the Issue.

When possible:

- Write or update tests before implementation.
- Commit coherent increments.
- Link commits and PRs to the Issue.

### 3.8 Verification

Run the verification commands relevant to the changed surface area.

Common commands:

```bash
cd apps/server && uv run pytest -q
cd apps/server && uv run ruff check .
npm run test -w apps/web
npm run build -w apps/web
```

For documentation-only changes, verify links, templates, and Markdown structure with local inspection.

Create or update a test report under:

```text
docs/tests/REQ-0000-short-name-test-report.md
```

when QA review or acceptance needs durable evidence.

### 3.9 Pull Request

Open a PR from the feature branch to `main`.

The PR must include:

- Linked Issue, using `Closes #<issue>` when appropriate.
- Registry file path and current phase/status.
- Requirement/design/plan links.
- Summary of changes.
- Verification commands and results.
- Risks, limitations, and rollback notes.

Do not merge without review.

### 3.10 Release

After merge to `main`, tag stable versions when a meaningful product baseline is reached.

Release notes should live under:

```text
docs/releases/RELEASE-YYYY-MM-DD.md
```

Record deployment environment and smoke-test evidence in the registry before moving to `deployed`.

### 3.11 Acceptance And Closure

Before closing the Issue:

- Confirm acceptance criteria are met.
- Confirm registry `phase: accepted`.
- Move the registry file from `docs/workflow/active/` to `docs/workflow/done/`.
- Link any follow-up Issues from the registry `notes` or `dependencies`.

---

## 4. Main Branch Policy

`main` represents the latest stable baseline.

Rules:

- No direct feature development on `main`.
- No unrelated cleanup in feature branches.
- No merge without review and verification evidence.
- Keep feature branches short-lived.
- Bug fixes should target `main` first, then be carried to release branches if such branches exist later.

---

## 5. Agent Workflow

Agents working in this repository must follow this sequence for non-trivial work:

1. Confirm or create the GitHub Issue.
2. Create or update the delivery registry file.
3. Clarify product requirements.
4. Write or update PRD/design docs when needed.
5. Write or update technical design and implementation plan.
6. Sync local `main` to `origin/main`.
7. Create a dedicated branch and worktree from the updated `main`.
8. Update the registry at each gate.
9. Implement only the approved scope.
10. Run verification.
11. Prepare PR-ready summary.

Agents must not treat an informal chat request as approval to skip the Issue, registry, branch, design, review, testing, deployment, or verification gates when the work is product or engineering significant.
