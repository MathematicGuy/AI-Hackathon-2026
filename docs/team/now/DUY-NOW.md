# DUY Current Mission

## Outcome

Deliver production-readiness hardening for the deployed advisor stack: remove
the shared-secret deploy path, bound the cost and abuse surface of the public
E02 agent endpoints, replace silent failure modes with observable ones, correct
the E02 Vietnamese persona in the chat UI, and make the comparison table render
from backend structured data instead of hardcoded frontend rows.

## Assignment

Lưu Tiến Duy owns US-125 — production readiness hardening, registered at
`docs/stories/epics/E06-delivery-automation/US-125-production-readiness-hardening/`.

Assigned by Duy (Lưu Tiến Duy) on 2026-07-19 after a repository audit of the
`deploy` branch found blocker-level deployment defects with no registered owner.

## Story Packet

- `docs/stories/epics/E06-delivery-automation/US-125-production-readiness-hardening/`

Contains `overview.md`, `design.md`, `execplan.md`, and `validation.md`.

## Dependency Order

1. P0 secrets and env contract — no code dependency, do first.
2. P1 agent endpoint limits — depends on P0 env contract for its config keys.
3. P2 backend observability and fail-fast — independent of P1.
4. P3 frontend persona, request timeouts, structured comparison — the
   comparison item depends on the P3a backend response field landing first.
5. P4 CI and deploy topology — independent; coordinates with US-124.

## Branch and Worktree

- Branch: `deploy` (current working branch, already checked out).
- No separate worktree: THANH's US-207 and this story overlap on
  `backend/app/agent/api.py`, so serialize rather than parallelize that file.

## Ownership boundary

US-125 owns only:

- `.env.example`, `docker-compose.production.yml`, root `docker-compose.yml`,
  `infra/nginx/default.conf`, `infra/backend.Dockerfile`
- `.github/workflows/ci.yml`
- `scripts/deploy-preflight.sh` (new)
- `backend/app/agent/api.py` (limits + logging only)
- `backend/app/agent/catalog/pg_adapter.py`, `backend/app/agent/llm/client.py`
- `backend/app/db/migrate.py`, `backend/app/ingestion/run.py` (logging only)
- the structured comparison field in the agent response contract
- `frontend/src/components/ChatbotAssistant.tsx`,
  `frontend/src/components/chat/ChatComparisonResult.tsx`,
  `frontend/src/components/LoginScreen.tsx`,
  `frontend/src/components/CheckoutScreen.tsx`,
  `frontend/src/components/AccountOrdersScreen.tsx`
- `frontend/package.json` metadata only

Do not edit E01 decision-engine files, Langfuse observability wiring owned by
THANH's US-207, another member's NOW file, or accepted product contracts.

## Coordination risk

`backend/app/agent/api.py` is also in scope for THANH's US-207 (root/API
lifecycle observability). Confirm with Thành before merging changes to that
file, or land US-125's changes first and let US-207 rebase.

## Current Status

Started 2026-07-19. Baseline recorded before implementation: backend suite
410 passed / 17 skipped; frontend `npm run check` baseline captured.

## Definition of Done

- Backend suite green before and after; no previously passing test regressed.
- New behavior covered by tests: rate limit rejection, oversized payload
  rejection, Postgres fail-fast, structured comparison payload shape.
- E02 live-tested against the running stack with the transcript that motivated
  the change; persona uses "em" / "anh, chị" in every user-visible string.
- Deploy drill from a clean host succeeds through the documented preflight.
- Harness proof and trace recorded; session log finalized.

## Frozen constraints

- Additive changes only; never break behavior that already works.
- E02 self-addresses as "em" and addresses the customer as "anh/chị".
- Comparison must be dimension-driven per category and must filter placeholder
  spec values before any claim.
- Never commit real credentials; rotate anything already exposed.
- Ignore `resources/`.
