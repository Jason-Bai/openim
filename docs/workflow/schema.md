# Delivery Registry Schema

Each active requirement has one YAML status file under `docs/workflow/active/`.

## Required Fields

```yaml
id: REQ-0000
title: Short requirement title
type: feature
status: active
phase: idea

github:
  issue: null
  issues: []
  pr: null
  prs: []

branch:
  name: null
  worktree: null

execution_items: []

docs:
  prd: null
  ux: null
  technical_design: null
  implementation_plan: null
  test_report: null
  release_note: null

reviews:
  product_review: pending
  ux_review: not_required
  technical_review: pending
  code_review: pending
  qa_review: pending

deployment:
  environment: null
  deployed_at: null
  smoke_test: null

timestamps:
  created_at: "YYYY-MM-DD"
  updated_at: "YYYY-MM-DD"

blockers: []
dependencies: []
notes: []
```

## Optional Multi-Issue Execution

When one approved requirement is split into multiple independently shippable execution Issues, keep the top-level `github.issue`, `github.pr`, `branch.name`, and `branch.worktree` as the primary or first active execution item for compatibility, and record the full set under `execution_items`.

```yaml
execution_items:
  - issue: https://github.com/OWNER/REPO/issues/1
    pr: https://github.com/OWNER/REPO/pull/2
    branch: feature/1-short-name
    worktree: /absolute/path/to/worktree
    phase: code_review
    status: active
```

## Allowed Values

### `type`

- `feature`
- `bug`
- `chore`
- `docs`
- `epic`

### `status`

- `active`
- `blocked`
- `done`
- `archived`

### `phase`

- `idea`
- `requirement_draft`
- `requirement_review`
- `requirement_approved`
- `ux_design`
- `ux_review`
- `technical_design`
- `technical_review`
- `planned`
- `development`
- `code_review`
- `testing`
- `qa_review`
- `ready_to_merge`
- `deployed`
- `accepted`
- `done`
- `archived`

### Review Fields

- `pending`
- `approved`
- `needs_changes`
- `rejected`
- `not_required`

## Gate Rules

- `requirement_approved` requires `reviews.product_review: approved`.
- `technical_review` requires `docs.technical_design`.
- `planned` requires `docs.implementation_plan`.
- `development` requires `branch.name` and `branch.worktree`, or at least one `execution_items` entry with branch and worktree.
- `code_review` requires `github.pr`, or at least one `execution_items` entry with `pr`.
- `testing` requires at least one verification command in the PR.
- `qa_review` requires `docs.test_report` unless explicitly waived in `notes`.
- `deployed` requires `deployment.environment` and `deployment.smoke_test`.
- `done` requires the file to move to `docs/workflow/done/`.

## Parallel Work Guidance

Parallel requirements should update separate registry files. If one requirement is intentionally split into multiple independent execution Issues, record them in `execution_items` and keep each Issue in its own branch/worktree.
