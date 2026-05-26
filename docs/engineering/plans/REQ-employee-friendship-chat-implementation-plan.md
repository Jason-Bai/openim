# Employee Friendship Approval And Direct Chat Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the smallest complete employee friend request approval flow: accept incoming requests, reject incoming requests, and keep employee direct chat guarded by accepted friendship.

**Architecture:** Use two vertical product slices rather than frontend/backend layer splits. Each slice adds one backend friendship action, wires the matching profile UI action, and verifies the relationship state through existing users/contacts/conversation APIs.

**Tech Stack:** FastAPI, SQLAlchemy, pytest, React, TypeScript, TanStack Query, Ant Design, Vite.

---

## Approved Inputs

- PRD: `docs/product/requirements/REQ-employee-friendship-chat.md`
- Technical design: `docs/engineering/REQ-employee-friendship-chat-technical-design.md`
- Registry: `docs/workflow/active/REQ-employee-friendship-chat.yml`

## Execution Issue Split

Create GitHub Issues only after this plan review is approved.

1. `Accept incoming friend request and enable employee direct chat`
2. `Reject incoming friend request and restore relationship to none`

Do not split backend and frontend into separate Issues. Each Issue must leave the app in a coherent product state.

## Pre-Development Gate

After this plan review is approved and the user confirms execution:

- Update registry `phase` to `planned`.
- Create the two GitHub Issues listed above.
- Sync local `main` to `origin/main`.
- Create one branch/worktree per Issue from updated `main`.
- Record the Issue links, branch names, and worktree paths in `docs/workflow/active/REQ-employee-friendship-chat.yml`.
- Move the relevant Issue registry phase to `development` only when its branch/worktree is ready.

## File Structure

- Modify `apps/server/app/api/friends.py`
  - Owns friend request creation and new accept/reject actions.
  - Keep the implementation inside this router because the current friendship behavior is already local to this file.
- Modify `apps/server/tests/test_p0_flow.py`
  - Add backend regression tests near existing friendship and employee direct chat tests.
  - Reuse existing helpers such as `register_user`, `auth_headers`, and `accept_friendship`.
- Modify `apps/web/src/api/openim.ts`
  - Add typed API helpers for accept/reject.
- Modify `apps/web/src/pages/App.tsx`
  - Add accept/reject mutations beside the existing add-friend mutation.
  - Add profile panel actions for `pending_in`.
  - Keep changes surgical; do not refactor the page component.
- Create `docs/tests/REQ-employee-friendship-chat-test-report.md`
  - Record final verification commands and outcomes after both Issues are complete.
- Modify `docs/workflow/active/REQ-employee-friendship-chat.yml`
  - Update issue links, branch/worktree path, PR link, test report path, and phase as gates progress.

## Chunk 1: Accept Incoming Friend Request

### Task 1: Add Backend Accept Endpoint

**Files:**
- Modify: `apps/server/tests/test_p0_flow.py`
- Modify: `apps/server/app/api/friends.py`

- [ ] **Step 1: Write failing tests for accepting an incoming request**

Add tests near `test_create_friend_request_updates_relationship`.

```python
def test_accept_incoming_friend_request_updates_relationships(client: TestClient) -> None:
    alice_id, alice_token = register_user(client, "alice", "E101", "Alice")
    bob_id, bob_token = register_user(client, "bob", "E102", "Bob")
    client.post(f"/api/friends/{bob_id}", headers=auth_headers(alice_token))

    response = client.post(f"/api/friends/{alice_id}/accept", headers=auth_headers(bob_token))

    assert response.status_code == 200
    assert response.json()["data"]["relationship"] == "friend"

    alice_users = client.get("/api/users", headers=auth_headers(alice_token)).json()["data"]["items"]
    bob_users = client.get("/api/users", headers=auth_headers(bob_token)).json()["data"]["items"]
    assert next(item for item in alice_users if item["id"] == bob_id)["relationship"] == "friend"
    assert next(item for item in bob_users if item["id"] == alice_id)["relationship"] == "friend"


def test_accept_incoming_friend_request_enables_direct_conversation(client: TestClient) -> None:
    alice_id, alice_token = register_user(client, "alice", "E101", "Alice")
    bob_id, bob_token = register_user(client, "bob", "E102", "Bob")
    client.post(f"/api/friends/{bob_id}", headers=auth_headers(alice_token))
    client.post(f"/api/friends/{alice_id}/accept", headers=auth_headers(bob_token))

    response = client.post(
        "/api/conversations/ensure",
        headers=auth_headers(alice_token),
        json={"target_type": "user", "target_id": str(bob_id)},
    )

    assert response.status_code == 200
    assert response.json()["data"]["conversation"]["target_id"] == str(bob_id)


def test_employee_message_after_accept_persists_for_both_users_and_pushes_events(
    client: TestClient, monkeypatch
) -> None:
    alice_id, alice_token = register_user(client, "alice", "E101", "Alice")
    bob_id, bob_token = register_user(client, "bob", "E102", "Bob")
    client.post(f"/api/friends/{bob_id}", headers=auth_headers(alice_token))
    client.post(f"/api/friends/{alice_id}/accept", headers=auth_headers(bob_token))
    alice_conversation = client.post(
        "/api/conversations/ensure",
        headers=auth_headers(alice_token),
        json={"target_type": "user", "target_id": str(bob_id)},
    ).json()["data"]["conversation"]
    pushed: list[tuple[int, dict[str, object]]] = []

    async def fake_send_to_user(user_id: int, payload: dict[str, object]) -> None:
        pushed.append((user_id, payload))

    monkeypatch.setattr("app.api.conversations.employee_ws_sessions.send_to_user", fake_send_to_user)

    response = client.post(
        f"/api/conversations/{alice_conversation['id']}/messages",
        headers=auth_headers(alice_token),
        json={"content": "hello bob", "content_type": "text"},
    )

    assert response.status_code == 200
    sent = response.json()["data"]["messages"][0]
    assert sent["content"] == "hello bob"

    alice_history = client.get(
        f"/api/conversations/{alice_conversation['id']}/messages",
        headers=auth_headers(alice_token),
    ).json()["data"]["items"]
    assert alice_history[-1]["content"] == "hello bob"
    assert alice_history[-1]["client_message_id"] == sent["client_message_id"]

    bob_conversations = client.get(
        "/api/conversations", headers=auth_headers(bob_token)
    ).json()["data"]["items"]
    bob_conversation = next(item for item in bob_conversations if item["target_id"] == str(alice_id))
    bob_history = client.get(
        f"/api/conversations/{bob_conversation['id']}/messages",
        headers=auth_headers(bob_token),
    ).json()["data"]["items"]
    assert bob_history[-1]["content"] == "hello bob"
    assert bob_history[-1]["client_message_id"] == sent["client_message_id"]
    assert [item[0] for item in pushed] == [bob_id, bob_id]
    assert [item[1]["type"] for item in pushed] == ["message.new", "conversation.updated"]
```

- [ ] **Step 2: Write failing test for wrong-side accept**

```python
def test_accept_friend_request_requires_incoming_request(client: TestClient) -> None:
    _, alice_token = register_user(client, "alice", "E101", "Alice")
    bob_id, _ = register_user(client, "bob", "E102", "Bob")
    client.post(f"/api/friends/{bob_id}", headers=auth_headers(alice_token))

    response = client.post(f"/api/friends/{bob_id}/accept", headers=auth_headers(alice_token))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
```

- [ ] **Step 3: Run focused backend tests and verify they fail**

Run:

```bash
cd apps/server && uv run pytest tests/test_p0_flow.py::test_accept_incoming_friend_request_updates_relationships tests/test_p0_flow.py::test_accept_incoming_friend_request_enables_direct_conversation tests/test_p0_flow.py::test_employee_message_after_accept_persists_for_both_users_and_pushes_events tests/test_p0_flow.py::test_accept_friend_request_requires_incoming_request -q
```

Expected: FAIL because `POST /api/friends/{user_id}/accept` is not implemented.

- [ ] **Step 4: Implement the minimal accept endpoint**

In `apps/server/app/api/friends.py`, add a helper to load incoming pending friendship and add the endpoint.

```python
@router.post("/{user_id}/accept")
def accept_friend_request(
    user_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(current_user)],
):
    friendship = incoming_pending_friendship(user_id, db, current)
    friendship.status = "accepted"
    db.commit()
    return ok({"relationship": "friend"}, request_id_from(request))


def incoming_pending_friendship(
    user_id: int,
    db: Session,
    current: User,
) -> Friendship:
    if user_id == current.id:
        raise ApiError("VALIDATION_FAILED", "不能处理自己的好友申请")
    target = db.get(User, user_id)
    if not target:
        raise ApiError("NOT_FOUND", "用户不存在")
    friendship = db.scalar(
        select(Friendship).where(
            Friendship.requester_id == user_id,
            Friendship.addressee_id == current.id,
            Friendship.status == "pending",
        )
    )
    if not friendship:
        raise ApiError("NOT_FOUND", "好友申请不存在")
    return friendship
```

- [ ] **Step 5: Run focused backend tests and verify they pass**

Run:

```bash
cd apps/server && uv run pytest tests/test_p0_flow.py::test_accept_incoming_friend_request_updates_relationships tests/test_p0_flow.py::test_accept_incoming_friend_request_enables_direct_conversation tests/test_p0_flow.py::test_employee_message_after_accept_persists_for_both_users_and_pushes_events tests/test_p0_flow.py::test_accept_friend_request_requires_incoming_request -q
```

Expected: PASS.

### Task 2: Wire Accept Action In The Web App

**Files:**
- Modify: `apps/web/src/api/openim.ts`
- Modify: `apps/web/src/pages/App.tsx`

- [ ] **Step 1: Add API helper**

In `apps/web/src/api/openim.ts`, add:

```ts
export function acceptFriend(token: string, userId: number) {
  return api<{ relationship: User["relationship"] }>(
    `/friends/${userId}/accept`,
    { method: "POST" },
    token
  );
}
```

- [ ] **Step 2: Import the helper in `App.tsx`**

Add `acceptFriend` to the existing import list from `../api/openim`.

- [ ] **Step 3: Add a local selected-profile relationship helper**

Add a local helper in `App.tsx` near `updateContactUserRelationship`. Use it for add, accept, and reject mutations so selected profile updates stay consistent.

```ts
function updateSelectedUserRelationship(
  current: SelectedView,
  userId: number,
  relationship: User["relationship"]
): SelectedView {
  return current.type === "profile" && current.target.type === "user" && current.target.user.id === userId
    ? {
        type: "profile",
        target: {
          type: "user",
          user: { ...current.target.user, relationship }
        }
      }
    : current;
}
```

- [ ] **Step 4: Add accept mutation beside add-friend mutation**

```ts
const acceptFriendMutation = useMutation({
  mutationFn: async (userId: number) => ({ userId, result: await acceptFriend(token, userId) }),
  onSuccess: ({ userId, result }) => {
    message.success("已添加好友");
    queryClient.setQueryData<{ items: User[] }>(["users"], (current) => ({
      items: (current?.items ?? []).map((item) =>
        item.id === userId ? { ...item, relationship: result.relationship } : item
      )
    }));
    queryClient.setQueryData<{ ai: ContactItem[]; all: ContactItem[] }>(["contacts"], (current) =>
      current ? updateContactUserRelationship(current, userId, result.relationship) : current
    );
    setSelected((current) => updateSelectedUserRelationship(current, userId, result.relationship));
    queryClient.invalidateQueries({ queryKey: ["contacts"] });
  },
  onError: (err) => {
    message.error(err instanceof ApiError ? err.message : "接受好友申请失败");
  }
});
```

- [ ] **Step 5: Pass accept props into `TargetProfile`**

Add props:

```ts
accepting={acceptFriendMutation.isPending}
onAcceptFriend={(userId) => acceptFriendMutation.mutate(userId)}
```

Update the `TargetProfile` prop type with:

```ts
accepting: boolean;
onAcceptFriend: (userId: number) => void;
```

- [ ] **Step 6: Show Accept button for `pending_in`**

Replace the current `pending_in` text-only state with an action area that keeps the text and adds an accept button.

```tsx
{target.user.relationship === "pending_in" && (
  <>
    <Typography.Text type="secondary">对方已申请添加你</Typography.Text>
    <Button type="primary" loading={accepting} onClick={() => onAcceptFriend(target.user.id)}>
      接受
    </Button>
  </>
)}
```

- [ ] **Step 7: Run frontend type/build checks**

Run:

```bash
npm run test -w apps/web
npm run build -w apps/web
```

Expected: both commands exit 0.

- [ ] **Step 8: Run full backend checks for this Issue**

Run:

```bash
cd apps/server && uv run pytest -q
cd apps/server && uv run ruff check .
```

Expected: pytest passes; ruff reports no issues.

- [ ] **Step 9: Commit Issue 1**

Run:

```bash
git add apps/server/app/api/friends.py apps/server/tests/test_p0_flow.py apps/web/src/api/openim.ts apps/web/src/pages/App.tsx
git commit -m "feat: accept incoming friend requests"
```

Expected: one commit containing only accept-flow code and tests.

## Chunk 2: Reject Incoming Friend Request

### Task 3: Add Backend Reject Endpoint

**Files:**
- Modify: `apps/server/tests/test_p0_flow.py`
- Modify: `apps/server/app/api/friends.py`

- [ ] **Step 1: Write failing tests for rejecting an incoming request**

Add tests near the accept tests.

```python
def test_reject_incoming_friend_request_resets_relationships(client: TestClient) -> None:
    alice_id, alice_token = register_user(client, "alice", "E101", "Alice")
    bob_id, bob_token = register_user(client, "bob", "E102", "Bob")
    client.post(f"/api/friends/{bob_id}", headers=auth_headers(alice_token))

    response = client.post(f"/api/friends/{alice_id}/reject", headers=auth_headers(bob_token))

    assert response.status_code == 200
    assert response.json()["data"]["relationship"] == "none"

    alice_users = client.get("/api/users", headers=auth_headers(alice_token)).json()["data"]["items"]
    bob_users = client.get("/api/users", headers=auth_headers(bob_token)).json()["data"]["items"]
    assert next(item for item in alice_users if item["id"] == bob_id)["relationship"] == "none"
    assert next(item for item in bob_users if item["id"] == alice_id)["relationship"] == "none"
```

- [ ] **Step 2: Write failing test for direct conversation remaining blocked after reject**

```python
def test_reject_incoming_friend_request_keeps_direct_conversation_blocked(client: TestClient) -> None:
    alice_id, alice_token = register_user(client, "alice", "E101", "Alice")
    bob_id, bob_token = register_user(client, "bob", "E102", "Bob")
    client.post(f"/api/friends/{bob_id}", headers=auth_headers(alice_token))
    client.post(f"/api/friends/{alice_id}/reject", headers=auth_headers(bob_token))

    response = client.post(
        "/api/conversations/ensure",
        headers=auth_headers(alice_token),
        json={"target_type": "user", "target_id": str(bob_id)},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
```

- [ ] **Step 3: Write failing test for wrong-side reject**

```python
def test_reject_friend_request_requires_incoming_request(client: TestClient) -> None:
    _, alice_token = register_user(client, "alice", "E101", "Alice")
    bob_id, _ = register_user(client, "bob", "E102", "Bob")
    client.post(f"/api/friends/{bob_id}", headers=auth_headers(alice_token))

    response = client.post(f"/api/friends/{bob_id}/reject", headers=auth_headers(alice_token))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
```

- [ ] **Step 4: Run focused backend tests and verify they fail**

Run:

```bash
cd apps/server && uv run pytest tests/test_p0_flow.py::test_reject_incoming_friend_request_resets_relationships tests/test_p0_flow.py::test_reject_incoming_friend_request_keeps_direct_conversation_blocked tests/test_p0_flow.py::test_reject_friend_request_requires_incoming_request -q
```

Expected: FAIL because `POST /api/friends/{user_id}/reject` is not implemented.

- [ ] **Step 5: Implement the minimal reject endpoint**

In `apps/server/app/api/friends.py`, reuse `incoming_pending_friendship`.

```python
@router.post("/{user_id}/reject")
def reject_friend_request(
    user_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(current_user)],
):
    friendship = incoming_pending_friendship(user_id, db, current)
    db.delete(friendship)
    db.commit()
    return ok({"relationship": "none"}, request_id_from(request))
```

- [ ] **Step 6: Run focused backend tests and verify they pass**

Run:

```bash
cd apps/server && uv run pytest tests/test_p0_flow.py::test_reject_incoming_friend_request_resets_relationships tests/test_p0_flow.py::test_reject_incoming_friend_request_keeps_direct_conversation_blocked tests/test_p0_flow.py::test_reject_friend_request_requires_incoming_request -q
```

Expected: PASS.

### Task 4: Wire Reject Action In The Web App

**Files:**
- Modify: `apps/web/src/api/openim.ts`
- Modify: `apps/web/src/pages/App.tsx`

- [ ] **Step 1: Add API helper**

In `apps/web/src/api/openim.ts`, add:

```ts
export function rejectFriend(token: string, userId: number) {
  return api<{ relationship: User["relationship"] }>(
    `/friends/${userId}/reject`,
    { method: "POST" },
    token
  );
}
```

- [ ] **Step 2: Import the helper in `App.tsx`**

Add `rejectFriend` to the existing import list from `../api/openim`.

- [ ] **Step 3: Add reject mutation beside accept mutation**

```ts
const rejectFriendMutation = useMutation({
  mutationFn: async (userId: number) => ({ userId, result: await rejectFriend(token, userId) }),
  onSuccess: ({ userId, result }) => {
    message.success("已拒绝好友申请");
    queryClient.setQueryData<{ items: User[] }>(["users"], (current) => ({
      items: (current?.items ?? []).map((item) =>
        item.id === userId ? { ...item, relationship: result.relationship } : item
      )
    }));
    queryClient.setQueryData<{ ai: ContactItem[]; all: ContactItem[] }>(["contacts"], (current) =>
      current ? updateContactUserRelationship(current, userId, result.relationship) : current
    );
    setSelected((current) => updateSelectedUserRelationship(current, userId, result.relationship));
    queryClient.invalidateQueries({ queryKey: ["contacts"] });
  },
  onError: (err) => {
    message.error(err instanceof ApiError ? err.message : "拒绝好友申请失败");
  }
});
```

- [ ] **Step 4: Pass reject props into `TargetProfile`**

Add props:

```ts
rejecting={rejectFriendMutation.isPending}
onRejectFriend={(userId) => rejectFriendMutation.mutate(userId)}
```

Update the `TargetProfile` prop type with:

```ts
rejecting: boolean;
onRejectFriend: (userId: number) => void;
```

- [ ] **Step 5: Add Reject button for `pending_in`**

Extend the `pending_in` action area:

```tsx
{target.user.relationship === "pending_in" && (
  <>
    <Typography.Text type="secondary">对方已申请添加你</Typography.Text>
    <Button type="primary" loading={accepting} onClick={() => onAcceptFriend(target.user.id)}>
      接受
    </Button>
    <Button loading={rejecting} onClick={() => onRejectFriend(target.user.id)}>
      拒绝
    </Button>
  </>
)}
```

- [ ] **Step 6: Run frontend checks**

Run:

```bash
npm run test -w apps/web
npm run build -w apps/web
```

Expected: both commands exit 0.

- [ ] **Step 7: Run full backend checks**

Run:

```bash
cd apps/server && uv run pytest -q
cd apps/server && uv run ruff check .
```

Expected: pytest passes; ruff reports no issues.

- [ ] **Step 8: Commit Issue 2**

Run:

```bash
git add apps/server/app/api/friends.py apps/server/tests/test_p0_flow.py apps/web/src/api/openim.ts apps/web/src/pages/App.tsx
git commit -m "feat: reject incoming friend requests"
```

Expected: one commit containing only reject-flow code and tests.

## Chunk 3: Final Verification And Delivery

### Task 5: Record Test Evidence And Prepare PR

**Files:**
- Create: `docs/tests/REQ-employee-friendship-chat-test-report.md`
- Modify: `docs/workflow/active/REQ-employee-friendship-chat.yml`

- [ ] **Step 1: Run full verification**

Run:

```bash
cd apps/server && uv run pytest -q
cd apps/server && uv run ruff check .
npm run test -w apps/web
npm run build -w apps/web
```

Expected:

- Backend pytest passes.
- Backend ruff passes.
- Frontend test/type check passes.
- Frontend build passes. Existing Vite chunk-size warning is acceptable if build exits 0.

- [ ] **Step 2: Create test report**

Create `docs/tests/REQ-employee-friendship-chat-test-report.md` with:

```markdown
# Employee Friendship Approval And Direct Chat Test Report

Date: 2026-05-26

## Scope

- Accept incoming friend request.
- Reject incoming friend request.
- Employee direct chat remains available only for accepted friendships.

## Verification

| Command | Result |
|---|---|
| `cd apps/server && uv run pytest -q` | PASS |
| `cd apps/server && uv run ruff check .` | PASS |
| `npm run test -w apps/web` | PASS |
| `npm run build -w apps/web` | PASS |

## Notes

- Relationship WebSocket events are out of scope.
- Outgoing request cancellation is out of scope.
```

- [ ] **Step 3: Update registry for code review**

Update `docs/workflow/active/REQ-employee-friendship-chat.yml`:

```yaml
phase: code_review
docs:
  test_report: docs/tests/REQ-employee-friendship-chat-test-report.md
reviews:
  code_review: pending
  qa_review: pending
```

Also fill `github.issue`, `github.pr`, `branch.name`, and `branch.worktree` after those exist.

- [ ] **Step 4: Commit verification docs**

Run:

```bash
git add docs/tests/REQ-employee-friendship-chat-test-report.md docs/workflow/active/REQ-employee-friendship-chat.yml
git commit -m "docs: record employee friendship verification"
```

Expected: one docs commit with final evidence and registry update.

- [ ] **Step 5: Open draft PR**

Push the implementation branch and open a draft PR against `main`.

PR body must include:

- Linked execution Issues.
- PRD, technical design, implementation plan, and test report links.
- Summary of accept and reject behavior.
- Verification commands and results.
- Explicit note that relationship WebSocket events and outgoing cancellation are out of scope.

Expected: draft PR is open and registry `github.pr` is updated.
