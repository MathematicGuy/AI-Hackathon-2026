# Exec Plan

## Goal

Make the `deploy` branch safe to run in production: no shared dev credentials,
a bounded public agent surface, observable failures instead of silent ones, a
correct E02 persona, and a comparison table that cannot contradict the agent.

## Scope

In scope:

- Dedicated production environment file; `.env.example` matched to the real
  contract consumed by the code.
- Rate limiting and payload caps on the public agent endpoints.
- Standard-library logging in place of `print`; feedback logging redacted.
- Fail-fast Postgres via `REQUIRE_POSTGRES`; logged LLM provider failures with
  one retry on transient errors.
- Structured, dimension-driven comparison payload on the agent response, and a
  frontend table that renders only from it.
- E02 persona corrections, chat request timeout, retry affordance, demo labels
  on the mock flows, and removal of the displayed OTP code.
- Frontend CI trigger corrected to the real default branch; stale root compose
  removed; deploy preflight script and README deploy path.

Out of scope:

- Real authentication, order placement, or order history.
- Durable agent session persistence (US-206).
- Langfuse observability wiring (US-207).
- Real NeMo Guardrails integration.
- Host, DNS, TLS, or managed-database provisioning.
- Credential rotation itself, which is a human action outside the repository.

## Risk Classification

Risk flags:

- Audit/security — secrets handling, redacted logging, abuse limits.
- External systems — LLM provider retry behavior, deployment topology.
- Public contracts — new optional field on the agent response envelope.
- Existing behavior — comparison rendering and persona strings change.
- Multi-domain — backend, frontend, and infrastructure change together.

Hard gates:

- Audit/security.
- External provider behavior.

Both hard gates are met by the high-risk lane: this packet, explicit human
direction on the three scope decisions, and validation before completion.

## Work Phases

1. Discovery — repository audit of backend, frontend, and deploy surfaces.
   Complete; findings recorded in `overview.md`.
2. Design — structured comparison projection and limit/observability approach.
   Complete; recorded in `design.md`.
3. Validation planning — test matrix in `validation.md`.
4. Implementation — P0 through P4 in dependency order.
5. Verification — full backend suite plus frontend build before and after, new
   unit coverage, and a live E02 run against the running stack.
6. Harness update — proof status and trace.

## Stop Conditions

Pause for human confirmation if:

- Rotating the exposed credentials turns out to require a repository change
  beyond removing them from the tracked contract.
- The structured comparison field cannot stay backward compatible.
- US-207's work on `backend/app/agent/api.py` lands first and conflicts.
- Removing the root compose file breaks a deploy path US-124 depends on beyond
  the already-agreed switch to `docker-compose.production.yml`.
