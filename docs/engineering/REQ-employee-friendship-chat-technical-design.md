# Employee Friendship Approval And Direct Chat Technical Design

Status: technical design approved; implementation plan reviewed

PRD: `docs/product/requirements/REQ-employee-friendship-chat.md`

Registry: `docs/workflow/active/REQ-employee-friendship-chat.yml`

---

## 1. Current Implementation

OpenIM already stores friendships in `friendships` with `requester_id`, `addressee_id`, and `status`.

Current relationship states exposed to the web app:

- `self`
- `none`
- `pending_out`
- `pending_in`
- `friend`

Implemented today:

- `POST /api/friends/{user_id}` creates a pending outgoing request.
- `GET /api/users` and `GET /api/contacts` derive relationship state from `friendships`.
- `POST /api/conversations/ensure` blocks `target_type=user` unless `users_are_friends(...)` is true.
- `POST /api/conversations/{conversation_id}/messages` also checks friendship before persisting user-to-user messages.
- The web profile panel can send a request, shows pending states, and only enables `Send message` for `friend`.

Missing:

- Recipient cannot accept an incoming request.
- Recipient cannot reject an incoming request.
- Web profile panel has no actions for `pending_in`.

## 2. Proposed Backend Design

Add two narrow friendship action endpoints:

- `POST /api/friends/{user_id}/accept`
- `POST /api/friends/{user_id}/reject`

Endpoint behavior:

- Both endpoints require authentication.
- `user_id` is the other employee's user id.
- Both endpoints reject self-actions with `VALIDATION_FAILED`.
- Both endpoints return `NOT_FOUND` when the target user does not exist.
- Both endpoints require an existing pending friendship where `requester_id == user_id` and `addressee_id == current.id`.
- If the pending incoming request does not exist, return `NOT_FOUND`.
- Accept changes `status` from `pending` to `accepted` and returns `{ relationship: "friend" }`.
- Reject deletes the pending friendship row and returns `{ relationship: "none" }`.

No database migration is required. The existing `pending` and `accepted` statuses are sufficient.

### Why Delete On Reject

The PRD approved the first-version rejection policy: rejected requests return both users to `none`, and the requester may re-request later. Deleting the pending row is the smallest implementation that matches this policy and avoids adding a new `rejected` state.

## 3. Proposed Frontend Design

Extend `apps/web/src/api/openim.ts` with:

- `acceptFriend(token, userId)`
- `rejectFriend(token, userId)`

Extend `apps/web/src/pages/App.tsx` with two mutations beside the existing add-friend mutation:

- Accept mutation:
  - Calls `acceptFriend`.
  - Updates `users` cache for the target user to `friend`.
  - Updates `contacts` cache for the target user to `friend`.
  - Updates the selected profile state if it is showing the same user.
  - Invalidates `contacts`.
- Reject mutation:
  - Calls `rejectFriend`.
  - Updates `users` cache for the target user to `none`.
  - Updates `contacts` cache for the target user to `none`.
  - Updates the selected profile state if it is showing the same user.
  - Invalidates `contacts`.

For `pending_in`, the profile panel should show two actions:

- `Accept`
- `Reject`

For `friend`, the existing `Send message` button remains unchanged.

## 4. Data Flow

Accept flow:

1. User B opens User A profile with `relationship=pending_in`.
2. User B clicks `Accept`.
3. Web calls `POST /api/friends/{alice_id}/accept`.
4. Backend verifies a pending row where Alice is requester and Bob is addressee.
5. Backend sets status to `accepted`.
6. Web updates local caches to `friend`.
7. User B can open a direct user conversation through the existing conversation endpoint.

Reject flow:

1. User B opens User A profile with `relationship=pending_in`.
2. User B clicks `Reject`.
3. Web calls `POST /api/friends/{alice_id}/reject`.
4. Backend verifies a pending row where Alice is requester and Bob is addressee.
5. Backend deletes the friendship row.
6. Web updates local caches to `none`.
7. Both users see no relationship after refresh.

## 5. Testing Strategy

Backend tests in `apps/server/tests/test_p0_flow.py`:

- Accepting an incoming friend request returns `friend`.
- After accept, both users see `friend`.
- After accept, direct conversation creation succeeds.
- Rejecting an incoming friend request returns `none`.
- After reject, both users see `none`.
- After reject, direct conversation creation remains blocked.
- Accept/reject from the requester side is rejected because it is not an incoming request.
- Existing non-friend message guardrail remains covered.

Frontend tests:

- Existing `npm run test -w apps/web` should pass after adding API functions and UI mutation wiring.
- Because the current frontend test suite is type/build oriented, no browser automation is required for the first implementation unless UI behavior regresses during manual smoke testing.

Full verification commands:

```bash
cd apps/server && uv run pytest -q
cd apps/server && uv run ruff check .
npm run test -w apps/web
npm run build -w apps/web
```

## 6. Issue Split Recommendation

Use independent minimal feature slices:

1. Accept incoming friend request and enable direct conversation.
2. Reject incoming friend request and return relationship to `none`.
3. Employee direct chat acceptance and regression coverage.

If the implementation plan shows the code changes are too small to justify three branches, merge these into one execution Issue after technical review approval. Do not split by backend/frontend layers.

## 7. Risks

- `apps/web/src/pages/App.tsx` is already carrying much of the page behavior. Keep this change surgical; do not refactor the component before this requirement.
- No real-time relationship WebSocket events are included. Other clients may need to refresh contacts to see relationship changes.
- Deleting on reject allows re-request. This is intentional for the first version.
