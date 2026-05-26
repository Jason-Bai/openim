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
| Repository docs | Durable PRD, UX design, technical design, implementation plan, release notes | `docs/` |
| Pull Request | Code review, CI, merge decision | GitHub Pull Requests |

Issues track and coordinate work. They do not replace durable docs for complex product, design, or technical decisions.

---

## 2. Work Types

### Epic

Use an Epic Issue for a product stage or large initiative, such as `P1: employee-to-bot chat`.

An Epic Issue should link child Feature/Bug Issues and describe the stage goal, scope boundary, sequencing, and release target.

### Feature

Use a Feature Issue for one independently shippable product or engineering capability.

Feature work requires:

- Feature Issue.
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

### 3.1 Product Requirement

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

### 3.2 UX/UI Design

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

### 3.3 Technical Design

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

### 3.4 Implementation Plan

Create an implementation plan under:

```text
docs/engineering/plans/REQ-0000-short-name.md
```

The plan should break work into small verifiable tasks. Each task should name files, tests, commands, and expected outcomes.

### 3.5 Branch And Worktree

Do not develop directly on `main`.

Branch naming:

```text
feature/<issue-number>-short-name
fix/<issue-number>-short-name
docs/<issue-number>-short-name
chore/<issue-number>-short-name
```

Use one worktree per independent Issue. Parallel work should not share one checkout.

### 3.6 Development

Follow the approved plan. Keep changes surgical and scoped to the Issue.

When possible:

- Write or update tests before implementation.
- Commit coherent increments.
- Link commits and PRs to the Issue.

### 3.7 Verification

Run the verification commands relevant to the changed surface area.

Common commands:

```bash
cd apps/server && uv run pytest -q
cd apps/server && uv run ruff check .
npm run test -w apps/web
npm run build -w apps/web
```

For documentation-only changes, verify links, templates, and Markdown structure with local inspection.

### 3.8 Pull Request

Open a PR from the feature branch to `main`.

The PR must include:

- Linked Issue, using `Closes #<issue>` when appropriate.
- Requirement/design/plan links.
- Summary of changes.
- Verification commands and results.
- Risks, limitations, and rollback notes.

Do not merge without review.

### 3.9 Release

After merge to `main`, tag stable versions when a meaningful product baseline is reached.

Release notes should live under:

```text
docs/releases/RELEASE-YYYY-MM-DD.md
```

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
2. Clarify product requirements.
3. Write or update PRD/design docs when needed.
4. Write or update technical design and implementation plan.
5. Create a dedicated branch and worktree.
6. Implement only the approved scope.
7. Run verification.
8. Prepare PR-ready summary.

Agents must not treat an informal chat request as approval to skip the Issue, branch, design, or verification gates when the work is product or engineering significant.
