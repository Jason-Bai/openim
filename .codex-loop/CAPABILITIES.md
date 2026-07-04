# Capability Fit Check

Every non-trivial project Loop phase must ask whether an existing skill, MCP
tool, connector, or local resource can make the phase more reliable.

## Required Record

For each meaningful phase, record:

```md
## Capability Fit

- Phase:
- Candidate capabilities:
- Used:
- Skipped with reason:
- Missing capability / follow-up:
```

## OpenIM Routes

- Discover: `rg`, project docs, `.superpowers/`, GitHub / CI when available.
- Intake: `systematic-debugging`, `brainstorming`, `.superpowers/` artifacts.
- Plan: `writing-plans`, `frontend-react-best-practices`, `ui-ux-pro-max`.
- Execute: `test-driven-development`, `acpx codex` for larger Maker handoffs,
  browser automation for browser-visible behavior.
- Verify: task-specific regression script or test first, then web test/build
  commands from `.codex-loop/VERIFY.md`.
- Checker: current git diff review, `requesting-code-review` when risk or
  blast radius is above low.
- Evolve: workspace `.codex-loop/EVOLUTION.md` when a reusable Loop weakness is
  discovered.

If a candidate is skipped, record why. A blank capability check is a Loop
defect.
