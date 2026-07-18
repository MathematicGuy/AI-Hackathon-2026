# US-115 Readable and Convenient Chatbot Frontend

## Status

in_progress

## Lane

normal

## Product Contract

The existing Next.js storefront chatbot in `frontend/` is easy to notice, read,
and operate on desktop and mobile. This mock-first slice is independent of
backend delivery: it improves the current conversation and comparison surfaces
without introducing a live API dependency. The UI renders supplied fields only;
it performs no client-side ranking, price math, eligibility, badge computation,
or evidence selection. Missing values stay visibly unknown and are never
inferred.

## Relevant Product Docs

- `docs/product/air-conditioner-advisor-m1-contract.md`
- `docs/product/requirements/air-conditioner-advisor-m1-prd.md` (§§4.14–4.18,
  16)
- `docs/product/architecture/air-conditioner-advisor-m1.md` (§§5.1, 7.5,
  8.2–8.4)

## Acceptance Criteria

- The launcher is noticeable without obscuring primary storefront actions.
- The chat panel fits common desktop and mobile viewports without horizontal
  overflow or unreachable controls.
- Header, conversation, comparison results, suggested prompts, and composer
  have a clear visual hierarchy and readable contrast.
- Customer and assistant messages are immediately distinguishable; timestamps
  and secondary metadata do not compete with answer content.
- The composer has an accessible name, visible focus, a clear send action, and
  prevents empty submissions without hiding the reason.
- Comparison results expose the recommendation, trade-offs, price, and next
  action in a scan-friendly order without changing supplied product truth.
- Existing storefront routes and behavior outside the chatbot remain unchanged.

## Design Notes

- Commands: `npm --prefix frontend run lint`, `typecheck`, and `build`.
- Queries: none; the live advisor endpoint remains out of scope.
- API: preserve the current mock-first component boundary.
- Tables: none (mock fixtures, no DB).
- Domain rules: supplied-fields-only rendering; never recompute recommendation
  truth.
- UI surfaces: launcher, chat shell, messages, prompt chips, composer, and
  comparison result.

## File Boundary

- `frontend/src/components/ChatbotAssistant.tsx`
- `frontend/src/components/chat/ChatComparisonResult.tsx`
- `frontend/src/app/globals.css`

## Implementation Plan

1. Capture desktop and mobile baselines and record concrete usability issues.
2. Apply the smallest component and style changes that improve hierarchy,
   readability, keyboard access, responsive fit, and action clarity.
3. Run static checks and production build, then capture matching visual proof
   for desktop and mobile.

## Validation

When updating durable proof status, use numeric booleans:
`scripts/bin/harness-cli story update --id US-115 --unit 1 --integration 0 --e2e 1 --platform 0`.

| Layer | Expected proof |
| --- | --- |
| Unit | No unit harness exists for this bounded visual change. |
| Integration | No backend integration; mock-first behavior only. |
| E2E | Manual interaction and screenshot proof for desktop and mobile. |
| Platform | Chromium desktop and mobile viewport checks. |
| Release | `npm --prefix frontend run lint && npm --prefix frontend run typecheck && npm --prefix frontend run build`. |

## Harness Delta

Normal-lane change request: existing user-visible behavior plus initially weak
visual proof, with no auth, data, provider, or API-contract change. The story is
registered independently from backend implementation and is owned by the
`FRONTEND` tracker.

## Evidence

Added after validation runs during plan execution.
