# US-125 Production Readiness Hardening

## Current Behavior

- `docker-compose.production.yml` loads the same `.env` used for local
  development, so a development database password and developer API keys are
  the production credential path.
- `POST /api/v1/agent/respond` and `/respond/stream` are publicly reachable
  with no rate limit and no request-size limit, so any caller can drive
  unbounded paid LLM traffic.
- `postgres_available()` catches every exception and silently falls back to the
  read-only Excel workbook, so a misconfigured database serves parallel data
  while startup still reports success.
- The backend has no logging framework; diagnostics use `print`, and agent
  feedback prints raw user message content to stdout.
- The chat comparison table renders three hardcoded air conditioners whenever a
  keyword heuristic matches, independent of what the agent actually answered.
- E02 user-visible strings in the chat UI address the customer as "mình" and
  "bạn" instead of "anh/chị", and the login screen displays the mock OTP code
  to the user.
- Chat requests have no timeout or cancellation, so a stalled backend leaves
  the UI spinning with no recovery path.
- `.github/workflows/ci.yml` triggers on `master`, which is not a branch in
  this repository, so frontend CI never runs.
- The root `docker-compose.yml` is a leftover website-cloner template with no
  backend and no database.

## Target Behavior

Production runs from a dedicated environment file with rotated credentials.
The public agent endpoints reject oversized payloads and excessive request
rates with explicit status codes. Database misconfiguration fails fast instead
of silently degrading. Backend diagnostics go through the standard logging
module and never record raw customer message content. The chat comparison table
renders only from a structured, dimension-driven payload returned by the
backend. Every E02 user-visible string addresses the customer as "anh/chị" and
the agent as "em". Chat requests time out and can be retried. Frontend CI runs
on the real default branch, and the documented deploy path points at the
production compose stack.

## Affected Users

- Operators deploying and running the production stack.
- Customers using the E02 sales agent in the storefront.
- Maintainers relying on CI to gate frontend regressions.

## Affected Product Docs

- `docs/product/architecture/multi-category-agent.md`
- `README.md`
- `.env.example`

## Non-Goals

- Building real authentication, order placement, or order history. Login,
  checkout, and account orders stay demo mocks and are labeled as such.
- Durable session persistence for the agent (remains US-206).
- Langfuse observability wiring (remains US-207).
- Integrating real NeMo Guardrails (deferred beyond Milestone 1).
- Provisioning hosts, DNS, TLS, or managed databases.
