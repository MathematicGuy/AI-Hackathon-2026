# 0009 M1 Explanation Model Routing

Date: 2026-07-17

## Status

Accepted

## Context

The approved M1 workflow assigned grounded recommendation explanations to
GPT-5.4 Mini. The product owner corrected that routing during the M1.0 contract
freeze: every M1 grounded explanation must use
`deepseek/deepseek-v4-flash` through OpenRouter instead.

Ranking remains deterministic. The explanation model receives only validated
needs, eligible products, deterministic winners, display selections, verified
evidence, calculated price differences, and allowed next-question candidates.

## Decision

Use `deepseek/deepseek-v4-flash` through OpenRouter for the M1 grounded
recommendation explainer. Do not use GPT-5.4 Mini in this role.

Keep GPT-5.4 Nano for intent classification and need extraction. Neither model
may filter, rank, select role winners, or override deterministic results.

## Alternatives Considered

1. Keep GPT-5.4 Mini. Rejected by the product owner.
2. Make the explanation model configurable per request. Rejected because M1.0
   freezes one deterministic routing contract.

## Consequences

Positive:

- Runtime routing matches the product owner's selected provider and model.
- Contract tests can reject model-name drift before later milestones integrate
  the provider.

Tradeoffs:

- M1.5 and later provider integration depends on OpenRouter availability and
  credentials.
- Provider failure behavior must remain deterministic and fail closed.

## Follow-Up

- M1.5 must implement the OpenRouter adapter without exposing credentials.
- M1.6 must prove grounded output validation and deterministic fallback.

