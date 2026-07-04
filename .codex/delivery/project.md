# Project Delivery Context

## Project
/Users/baiyu/.openclaw/workspace/projects/openim

## Global Goal
Use the existing OpenIM project as the base for a publishable Workspace MVP inspired by the Stitch design. Delivery must be decomposed into independently verifiable slices before implementation.

## Active Releases
- openim-workspace-mvp: planned

## Active Work Items
- loop-mvp: prototype spike, not a release branch
- openim-workspace-mvp-baseline
- openim-workspace-mvp-login-shell
- openim-workspace-mvp-chat-layout
- openim-workspace-mvp-task-static
- openim-workspace-mvp-app-center
- openim-workspace-mvp-release-polish

## Blocked Work Items

## Merge Queue

## Shared Decisions

## Global Constraints

## Standard Verification Commands
- npm run build -w apps/web
- npm run test -w apps/web

## Deployment Model

## Known Risks

## Cross-Worktree Conflicts

## Loop Control

active_loop:
loop_signal: release-too-broad
feedback_queue:
next_action: use decomposition-loop and implement release slices instead of continuing the prototype spike as the release branch
learning_log:
- source: loop-mvp prototype
  lesson: A publishable MVP is too broad for one work item; split it into baseline, shell, layout, static feature slices, and release polish.

## Final Project Handoff
