# Exec Plan

## Goal

Create an executable M1.0 contract freeze that blocks schema, node-name,
model-routing, and fixture drift.

## Scope

In scope:

- Product contract and DeepSeek routing decision.
- Contract schemas and graph-name/order constants.
- Mock recommendation payload and ten smoke scenarios.
- Dataset integrity, golden regression, and contract tests.

Out of scope:

- Runtime workflow behavior from M1.1–M1.4.
- Provider calls, production ranking, persistence, UI, and deployment.

## Risk Classification

Risk flags:

- External systems.
- Public contracts.
- Existing behavior.
- Weak proof.

Hard gates:

- External provider routing.

## Work Phases

1. Freeze the product and architecture decision documents.
2. Write failing contract and fixture-integrity tests.
3. Implement the minimum schemas, constants, and fixtures required to pass.
4. Run focused and complete M1.0 proof.
5. Record story proof, trace, audit, and proposals.

## Stop Conditions

Pause for human confirmation if:

- A contract conflicts with the explicit DeepSeek routing correction.
- Production ranking weights would need approval.
- Validation requirements would need to be weakened.

