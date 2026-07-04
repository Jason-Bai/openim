# Execution Adapter

This file defines how the Outer Loop delegates implementation and review work
to coding agents.

## Current Adapter

Preferred headless adapter: `acpx` calling Codex through ACP.

Built-in `acpx` agent name:

```bash
codex
```

Project cwd:

```bash
/Users/baiyu/.openclaw/workspace/projects/openim
```

## Maker Execution

Use a one-shot Maker run when the task can be completed in one turn:

```bash
acpx codex exec \
  --cwd /Users/baiyu/.openclaw/workspace/projects/openim \
  --approve-all \
  --timeout 600 \
  --file .codex-loop/PROMPTS/maker.md
```

Use a persistent Maker session for multi-turn repair loops:

```bash
acpx codex sessions new --cwd /Users/baiyu/.openclaw/workspace/projects/openim --name maker
acpx codex prompt \
  --cwd /Users/baiyu/.openclaw/workspace/projects/openim \
  --session maker \
  --approve-all \
  --timeout 600 \
  --file .codex-loop/PROMPTS/maker.md
```

Maker may edit files and run local commands. Keep Maker scoped to
`.codex-loop/STATE.md`.

## Checker Execution

Checker should review only and should not write files:

```bash
acpx codex exec \
  --cwd /Users/baiyu/.openclaw/workspace/projects/openim \
  --approve-reads \
  --timeout 600 \
  --file .codex-loop/PROMPTS/checker.md
```

If Checker reports `FAIL`, update `.codex-loop/STATE.md` with the required
fixes and re-run Maker unless `Iteration Count` has reached `Max Iterations`.

## Verifier Execution

Verifier can be run by OpenClaw directly with shell commands from
`.codex-loop/VERIFY.md`, or delegated:

```bash
acpx codex exec \
  --cwd /Users/baiyu/.openclaw/workspace/projects/openim \
  --approve-reads \
  --timeout 600 \
  --file .codex-loop/PROMPTS/verifier.md
```

OpenClaw remains responsible for deciding whether the loop advances, iterates,
or stops. Verification must come from objective command output.

## Permission Policy

- Maker: `--approve-all` only in a controlled local worktree or when the user
  has explicitly authorized code edits.
- Checker: `--approve-reads`.
- Verifier: prefer direct shell commands; otherwise `--approve-reads`.
- External actions such as push, PR creation, merge, email, or public posting
  require explicit user approval.
