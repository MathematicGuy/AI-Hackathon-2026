# 0017 E02 Structured Chatbot Presentation

Date: 2026-07-19

## Status

Accepted

## Context

The storefront chatbot in `frontend/` already calls the shipped E02 endpoint,
`POST /api/v1/agent/respond`. The endpoint returns grounded prose plus intent
and identifier metadata, while the frontend independently recognizes a
comparison request and renders hard-coded products, prices, badges, attributes,
links, ratings, and follow-up prompts. This can show a rich comparison that does
not match the server response.

ADR-0015 makes the generic E02 agent the product direction and keeps the
air-conditioner M1 advisor as an evaluation rig. The storefront therefore must
not switch to the unimplemented M1 `/api/v1/advisor/respond` route or reuse
`frontend-mvp/`.

## Decision

1. Keep `POST /api/v1/agent/respond` and its request shape as the storefront
   chatbot boundary.
2. Extend its response additively with a server-owned `presentation`
   discriminator and render-ready data for text, recommendation, and comparison
   states. Keep the existing top-level `text` field as the compatibility and
   failure fallback.
3. Build presentation data from the same verified product and comparison
   records used to produce the grounded answer. Rich product presentation is
   emitted only when every selected record has a non-empty, unique `sku`.
   `productidweb` remains nullable because the current generic record can
   conflate it with a SKU fallback; do not require the browser to hydrate
   ambiguous identifiers through a second catalog request.
4. The server owns product roles/badges, prices, promotions, selected comparison
   rows, warnings, and follow-up prompts. The frontend renders supplied values
   and does not parse prose or recalculate product truth.
5. Image, product URL, rating, sold count, and any other unavailable field are
   nullable. The frontend uses an honest placeholder or omits the related
   action; it never substitutes hard-coded catalog facts.
6. Deploy the additive backend contract before the frontend starts depending on
   `presentation`. Older responses remain usable through `text`.

## Alternatives Considered

1. Return only stable SKUs and let the frontend call catalog endpoints. Rejected
   because it introduces a second request, exposes raw attribute mapping to the
   client, and can drift from the records used to compose the answer.
2. Remove the hard-coded table and keep a text-only UI. Safe but rejected as the
   target because it does not satisfy the intended structured storefront
   experience.
3. Use the M1 `/api/v1/advisor/respond` contract or `frontend-mvp/`. Rejected
   because that route is not mounted in the shipped app and ADR-0015 classifies
   the M1 path as an evaluation rig.

## Consequences

Positive:

- Rich chatbot UI and grounded server output share one source of truth.
- The change is backward-compatible during deployment.
- Generic comparison rendering works across E02 categories without copying
  air-conditioner-specific schemas.

Tradeoffs:

- The E02 API response becomes larger and needs explicit contract tests.
- Backend code must preserve structured presentation data instead of discarding
  it after prose rendering.
- Missing visual enrichment remains visibly unavailable until an authoritative
  source exists.

## Follow-Up

- Execute US-125 after an E02 backend owner and exact backend file boundary are
  assigned in the tracker/Harness coordination records.
- Add contract, integration, frontend rendering, and cross-stack E2E proof
  before marking US-125 implemented.
