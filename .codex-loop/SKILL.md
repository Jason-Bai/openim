# Codex Loop Project Rules

## Project

OpenIM workspace MVP.

## Role

OpenClaw acts as the Outer Loop orchestration layer:

```text
Discover -> Plan -> Execute -> Verify -> Checker -> Iterate / Summarize
```

Maker changes must stay scoped to `.codex-loop/STATE.md`.

## Project Context

- Root package: npm workspaces
- Web app: `apps/web`
- Backend: `apps/server`
- Plugin package: `packages/openclaw-bot-plugin`
- Existing delivery context: `.codex/delivery/`

## Standard Verification

Use `.codex-loop/VERIFY.md` for the active task. Existing project constraints
also require:

```bash
npm run build -w apps/web
npm run test -w apps/web
```

## Execution Adapter

Use `.codex-loop/EXECUTION.md` for delegation mechanics. The preferred
headless path is `acpx` calling Codex through ACP:

```bash
acpx codex exec --cwd /Users/baiyu/.openclaw/workspace/projects/openim --file .codex-loop/PROMPTS/maker.md
```

OpenClaw remains the Outer Loop owner. Maker performs code changes. Checker
reviews diff only. Verifier runs objective commands.

## Editing Rules

- Keep changes surgical.
- Do not touch existing unrelated dirty files.
- Do not develop broad product scope on `main`.
- For this loop smoke task, only edit `.codex-loop/` plus the minimal backend
  test and service files required for the selected bug.
- Do not treat LLM judgment as final verification.
- Stop after 3 iterations or on high-risk changes.
