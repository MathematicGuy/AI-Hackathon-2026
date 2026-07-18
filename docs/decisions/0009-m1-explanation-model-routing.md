# 0009 M1 Environment-Owned Model Routing

Date: 2026-07-17

## Status

Accepted

## Context

M1 needs independently configurable runtime routes without embedding provider
or model identifiers in application code, contracts, plans, or customer-runtime
documentation. Ranking remains deterministic. Model routes receive only the
validated inputs allowed by their role and cannot filter, rank, select role
winners, or override deterministic results.

## Decision

Load four required runtime roles from the operator environment:

- `main` handles intent classification and grounded recommendation explanation;
- `extraction` handles structured need extraction;
- `fallback` is the second route for `main` and `extraction` workloads;
- `judge` handles model-based evaluation and has no fallback.

Intent classification and grounded explanation use the immutable order
`main` then `fallback`. Need extraction uses `extraction` then `fallback`.
Judge failures fail closed and produce no substituted score.

Each role's provider and model identifier, together with each provider's base
URL and credential, is supplied through the canonical environment settings.
Operator model or provider swaps therefore require only an environment change.
Changing role responsibilities, route order, or failure policy still requires
architecture and ADR review.

## Alternatives Considered

1. Keep model identifiers in code or documentation. Rejected because routine
   operator changes would require repository edits and could drift across
   runtime boundaries.
2. Make routing configurable per request. Rejected because M1 freezes one
   composition-time routing contract rather than exposing routing to callers.
3. Give judge evaluation a fallback. Rejected because substituting a different
   judge could silently change evaluation semantics.

## Consequences

Positive:

- Operators can change model identifiers without changing tracked artifacts.
- Classification, extraction, explanation, and judge responsibilities remain
  explicit and independently testable.
- Route order is immutable after configuration bootstrap.

Tradeoffs:

- Startup fails when any required role or provider setting is missing or
  invalid.
- Provider outages exhaust the configured route order before deterministic
  runtime fallback behavior applies.
- Judge unavailability blocks the score instead of substituting another route.

## Follow-Up

- Provider adapters must consume the resolved role routes through dependency
  injection without exposing credentials.
- Grounded output validation and deterministic response fallback remain
  mandatory after configured explanation routes are exhausted.
