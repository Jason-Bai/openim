# Employee Friendship Approval And Direct Chat PRD

Status: PRD approved; technical design in review

Registry: `docs/workflow/active/REQ-employee-friendship-chat.yml`

---

## 1. Summary

OpenIM already has employee contacts, outgoing friend requests, backend user-to-user conversation rules, and backend-backed message persistence. The product flow is incomplete because an employee can send a friend request, but the recipient cannot accept or reject it in the UI.

This requirement completes the smallest useful employee-to-employee flow: send a friend request, accept or reject it, and allow direct chat only after friendship is established.

## 2. Problem

Today, the system can represent these relationship states:

- `none`
- `pending_out`
- `pending_in`
- `friend`
- `self`

However, only the outgoing request action exists in the product UI. When User A sends a friend request to User B, User B can see an incoming request state but cannot act on it. Because direct employee chat requires `friend`, the employee-to-employee chat workflow cannot be completed through the normal UI.

## 3. Goals

- Let a recipient accept an incoming friend request.
- Let a recipient reject an incoming friend request.
- Keep relationship state accurate in contacts and profiles after each action.
- Let friends open a direct conversation and send messages.
- Continue blocking non-friend direct conversations and messages.

## 4. Non-Goals

- Friend groups.
- Removing an existing friend.
- Blocking or reporting users.
- Friend request notifications center.
- Unread counts.
- Group chat, zones, sub-zones, or file messages.
- Real-time friend relationship WebSocket events.
- Admin management for friendships.

## 5. Users

Primary users:

- Employees who need to chat with other employees in OpenIM.

Secondary users:

- Developers validating the employee chat model before larger IM features.

## 6. User Stories

- As User A, I want to send a friend request to User B so that I can start a direct chat after approval.
- As User B, I want to accept an incoming friend request so that User A and I become friends.
- As User B, I want to reject an incoming friend request so that the relationship does not become a friend relationship.
- As an employee, I want non-friend direct chat to remain blocked so that people cannot message me before a relationship exists.
- As a developer/tester, I want the direct chat flow to be verifiable through backend tests and local smoke checks.

## 7. Proposed Behavior

### 7.1 No Relationship

When User A views User B and no relationship exists:

- UI shows `Add friend`.
- User A can send a friend request.
- User A then sees `pending_out`.
- User B sees `pending_in`.

### 7.2 Incoming Request

When User B views User A and the relationship is `pending_in`:

- UI shows `Accept` and `Reject`.
- Accept changes the relationship to `friend` for both users.
- Reject removes the pending relationship and returns both users to `none`.

### 7.3 Friend Relationship

When both users are friends:

- UI shows `Send message`.
- Either user can open a direct employee conversation.
- Messages are persisted in both users' conversation histories.
- If the receiver has an active employee WebSocket connection, the receiver gets `message.new` and `conversation.updated`.

### 7.4 Non-Friend Guardrail

If users are not friends:

- Direct conversation creation remains blocked.
- Direct message sending remains blocked.

## 8. Rejection Policy

First version policy:

- Rejecting a friend request deletes or neutralizes the pending request.
- Both users return to `none`.
- The requester may send another request later.

Rationale:

- This keeps the first version simple.
- It avoids a new persistent `rejected` state and extra UI explanations.
- Anti-spam controls can be designed later if needed.

## 9. Acceptance Criteria

- User A can send a friend request to User B.
- User A sees `pending_out` after sending the request.
- User B sees `pending_in` for User A.
- User B can accept the request.
- After acceptance, both users see `friend`.
- After acceptance, either user can open a direct conversation.
- After acceptance, either user can send a text message.
- The sender's conversation history contains the message.
- The receiver's conversation history contains the message.
- If the receiver is connected to `/ws`, the receiver gets `message.new` and `conversation.updated`.
- User B can reject an incoming request.
- After rejection, both users see `none`.
- Non-friends cannot create or send direct employee conversations.
- Existing default BOT and OpenClaw BOT flows continue to pass existing tests.

## 10. Issue Split Guidance

After PRD and technical design approval, GitHub Issues should be split by independent minimal feature slices, not by default frontend/backend layers.

Suggested split:

1. Accept incoming friend request and enable direct conversation.
2. Reject incoming friend request and return relationship to `none`.
3. Employee direct chat verification and acceptance coverage.

If technical design shows the total implementation is small enough, these may be merged into one execution Issue.

## 11. Risks And Open Questions

- Whether rejection should delete the friendship row or persist a `rejected` state. Recommendation: avoid `rejected` in the first version.
- Whether outgoing request cancellation should be included. Recommendation: out of scope for this requirement.
- Whether relationship changes should be pushed over employee WebSocket. Recommendation: out of scope for the first version; refresh contacts after actions.
- Whether frontend `App.tsx` should be refactored before adding more profile actions. Recommendation: keep implementation surgical unless technical design shows refactoring is necessary.

## 12. Review Questions

1. Should rejected requests return both users to `none` and allow future re-request?
2. Should outgoing request cancellation be excluded from this requirement?
3. Should real-time relationship update events be excluded from the first version?
4. Should the first implementation be one Issue or split into the three minimal feature slices listed above?
