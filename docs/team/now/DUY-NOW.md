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

Lưu Tiến Duy also owns US-126 — the isolated representative category-brand
image pilot, registered at
`docs/stories/epics/E05-dmx-catalog/US-126-representative-category-brand-images/`.
This second story was explicitly directed by Duy on 2026-07-19 after replacing
the earlier SKU-level image-search design. After the five-group review passed,
Duy explicitly promoted US-126 to the all-group mapping, Agent API projection,
and disclosed chatbot rendering on the same date.

Assigned by Duy (Lưu Tiến Duy) on 2026-07-19 after a repository audit of the
`deploy` branch found blocker-level deployment defects with no registered owner.

## Story Packet

- `docs/stories/epics/E06-delivery-automation/US-125-production-readiness-hardening/`
- `docs/stories/epics/E05-dmx-catalog/US-126-representative-category-brand-images/`

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

US-126 owns only:

- `backend/app/catalog_images/`
- `backend/tests/unit/catalog_images/`
- `scripts/collect_representative_images.py`
- `backend/app/agent/api.py` (representative-image projection only)
- `backend/tests/contract/test_agent_api_contract.py` (image contract only)
- `frontend/src/components/ChatbotAssistant.tsx` (image rendering only)
- `frontend/public/images/products/representative-placeholder.svg`
- `docs/product/architecture/multi-category-agent.md` (image projection only)
- `docs/decisions/0018-versioned-representative-category-brand-images.md`
- its own story packet and local git-ignored operational output under
  `data/processed/representative-images/`

Do not edit E01 decision-engine files, Langfuse observability wiring owned by
THANH's US-207, another member's NOW file, or accepted product contracts.

## Coordination risk

`backend/app/agent/api.py` retains THANH's completed US-207 root/API lifecycle
observability. US-126 changes only the response projection after that work and
must keep the observer calls and flush behavior intact. The same file and
chatbot component also contain Lưu Tiến Duy's US-125 hardening; serialize the
US-126 edits after those existing changes.

## Current Status

Started 2026-07-19. Baseline recorded before implementation: backend suite
410 passed / 17 skipped; frontend `npm run check` baseline captured.

US-126 pilot baseline (2026-07-19): the bounded live run completed; five
configured category-brand pages produced three representative image URLs each
(15 total, 5 ready, 0 not_found, 0 error). Mapping and review files are under
the ignored `data/processed/representative-images/pilot-5/` directory. The
subsequent promotion below adds the runtime projection and guarded collector;
the pilot itself never wrote catalog rows.

US-126 promotion status (2026-07-19): implementation is complete for explicit
all-group collection, versioned runtime mapping, stable SKU projection, Agent
API fields, common placeholder, and disclosed chatbot rendering. Focused tests
are 63 passed; the full backend suite is 500 passed / 17 skipped; frontend lint,
typecheck, and production build pass. The pilot resume reports 5 ready groups
and 15 images. The catalog derives 238 unique groups (234 source-backed and 4
placeholder-only). The all-group crawl has not been invoked because the CLI
requires an explicit `--all-groups`; no catalog/database write is implicit.
Browser screenshot proof is still pending after the local dev/CDP session was
interrupted.

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
