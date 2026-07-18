# US-115 Approved Mock-First Frontend

## Status

planned

## Lane

normal

## Product Contract

A testing-only Next.js frontend (`frontend/`) renders all 8
`RecommendationOutput.answer_type` states from mock fixtures and is swappable to
the real advisor backend by flipping one env var
(`NEXT_PUBLIC_ADVISOR_MODE=mock|live`). The UI renders server-owned fields only:
no client-side ranking, price math, eligibility, badge computation, or evidence
selection. Missing fields render `"không có"` (text) or `"chưa rõ"`
(numeric/price), never inferred.

## Relevant Product Docs

- `ARCHITECTURE.md` (§5.5–5.6 API contract, §7–8 `RecommendationOutput` shape)
- `WORKFLOW-MVP(4).md`
- `docs/superpowers/specs/2026-07-17-frontend-mvp-design.md`
- `docs/superpowers/plans/2026-07-17-frontend-mvp.md`

## Acceptance Criteria

- All 8 `answer_type` states render from mock data, each reachable by a keyword
  trigger, each wrapper carrying `data-testid="answer-${answer_type}"`.
- Data flows exclusively through `sendMessage` in `lib/advisor-api.ts`; no
  component imports mock fixtures directly.
- Only the three formal roles (`best_overall`, `best_value`,
  `cheapest_qualified`) exist; `best_for_primary_priority` is a display badge.
- A product with multiple badges renders once, badges merged by `product_id`.
- Switching to the live backend requires only env changes, no component or type
  edits.

## Design Notes

- Commands: n/a (read-only client).
- Queries: `POST /api/v1/advisor/respond` (mirrored, not owned).
- API: `sendMessage(req: AdvisorRequest): Promise<AdvisorResponse>` single swap
  point on `NEXT_PUBLIC_ADVISOR_MODE`.
- Tables: none (mock fixtures, no DB).
- Domain rules: server-owned-fields-only rendering; dedup by `product_id`.
- UI surfaces: chat shell + `AnswerRenderer` dispatch over 8 answer-type
  components.

## Validation

When updating durable proof status, use numeric booleans:
`scripts/bin/harness-cli story update --id US-115 --unit 1 --integration 0 --e2e 1 --platform 0`.

| Layer | Expected proof |
| --- | --- |
| Unit | Vitest over `lib/` pure utilities (ids, format, dedupe, scenario matcher). |
| Integration | n/a (no backend in mock mode). |
| E2E | Playwright drives all 8 answer_types; asserts dedup (one card, two badges). |
| Platform | Browser only. |
| Release | `npm run typecheck && npm run test && npm run build && npm run test:e2e`. |

## Harness Delta

Story created at intake for build-type work per `docs/FEATURE_INTAKE.md`
(normal lane, 0–1 flags, no hard gates). Executes
`docs/superpowers/plans/2026-07-17-frontend-mvp.md`.

## Evidence

Added after validation runs during plan execution.
