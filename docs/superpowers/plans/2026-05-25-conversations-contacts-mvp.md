# Conversations Contacts MVP Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the MVP interaction where conversations and contacts are separate, contacts open profiles first, and only user action creates a conversation.

**Architecture:** Backend owns relationship truth with a minimal `friendships` table and returns relationship/presence fields from `/api/users`. Frontend owns selection state with two primary modes: `sessions` and `contacts`; contacts show profiles, and "发消息" creates/activates a local conversation entry.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, pytest, React, Vite, TanStack Query, Ant Design.

---

## Chunk 1: Backend Relationship MVP

### Task 1: Friendships Model And API

**Files:**
- Create: `apps/server/app/models/friendship.py`
- Create: `apps/server/app/api/friends.py`
- Modify: `apps/server/app/models/__init__.py`
- Modify: `apps/server/app/models/user.py`
- Modify: `apps/server/app/api/users.py`
- Modify: `apps/server/app/main.py`
- Modify: `apps/server/alembic/versions/0001_p0_schema.py`
- Test: `apps/server/tests/test_p0_flow.py`

- [ ] Write failing tests for `/api/users` relationship values and `POST /api/friends/{user_id}`.
- [ ] Run the targeted backend test and confirm it fails because relationships are missing.
- [ ] Implement minimal friendship model, API, relationship derivation, and presence fields.
- [ ] Run targeted backend tests and full backend checks.

## Chunk 2: Frontend Conversation/Contact MVP

### Task 2: Frontend State And Panels

**Files:**
- Modify: `apps/web/src/api/openim.ts`
- Modify: `apps/web/src/pages/App.tsx`
- Modify: `apps/web/src/styles.css`

- [ ] Add API types and `addFriend`.
- [ ] Add selected menu/target state and local session list state.
- [ ] Render empty conversation guide by default.
- [ ] Render contact profile with relationship and add-friend button.
- [ ] Render AI list without status words, using green online dots only.
- [ ] Render sessions list only after user clicks "发消息".
- [ ] Build frontend and run MVP E2E.
