# US-125 Overview — Structured Storefront Chatbot Presentation

## Status

in_progress

## Lane

high-risk

## Ownership and Dependencies

- Coordination and `frontend/` owner: `FRONTEND` / Nguyễn Phương Hoài Ngọc.
- Branch/worktree: `deploy` / `E:\VAI\AI-Hackathon-2026`.
- Backend presentation-contract owner: `FRONTEND` / Nguyễn Phương Hoài Ngọc for
  only the exact files listed in `docs/team/now/FRONTEND-NOW.md`, assigned by
  Ngọc's explicit human direction on 2026-07-19. Cường retains other E02 scope.
- Durable API decision: ADR-0017.
- The backend contract/test slice runs before frontend consumption on `deploy`.

## Current Behavior

`frontend/src/components/ChatbotAssistant.tsx` already posts messages to
`/api/v1/agent/respond` and preserves the returned session ID. It narrows the
response to text, classifies comparison requests with a client-side query
regex, and mounts `ChatComparisonResult` without response data.

`ChatComparisonResult` contains static air-conditioner products, prices,
badges, specifications, ratings, links, and follow-up questions. The shipped E02
API returns `session_id`, `request_id`, `intent`, `text`, `flags`, and
`presented_ids`, but no render-ready product or comparison payload. A server
clarification can therefore appear beside an unrelated hard-coded table.

## Target Behavior

The shipped E02 endpoint returns an additive, server-owned `presentation`
payload matching the data needed by the storefront chatbot. `frontend/` stores
the typed response and renders text, recommendations, or comparisons from its
discriminator. Product cards, rows, badges, prices, promotions, warnings, and
follow-up prompts come from the server; the query regex and static comparison
catalog are removed.

The existing `text` field remains a fallback for old deployments, errors, and
text-only states. If the server has not selected enough products for a
comparison, the frontend displays the server's clarification only and does not
show a comparison table.

## Affected Users

- Storefront shoppers using the chatbot on desktop or mobile.
- Backend and frontend maintainers coordinating the E02 response contract.

## Affected Product Docs

- `docs/decisions/0015-multi-category-agent-pivot.md`
- `docs/decisions/0017-e02-structured-chatbot-presentation.md`
- `docs/product/architecture/multi-category-agent.md`
- `docs/stories/epics/E01-air-conditioner-advisor-m1/US-124-independent-chatbot-ux.md`

## Non-Goals

- Modifying or consuming `frontend-mvp/`.
- Mounting the M1 `/api/v1/advisor/respond` route.
- Adding streaming, authentication, durable conversation persistence, catalog
  migrations, new ranking rules, or fabricated visual enrichment.
- Making the frontend infer roles, prices, evidence, attributes, or product
  identity from prose.
