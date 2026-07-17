# US-121 Executable Contract Reconciliation

## Current Behavior

M1.0 freezes the common trace, response envelope, and minimal cards, but later approved workflow requirements need a public error envelope, one conditional recovery span, and a truthful display-only alternative badge. No backend dependency manifest exists.

## Target Behavior

Add only the backward-compatible contract elements required to execute M1.1–M1.8, document their authority, and prove the existing M1.0 fixture remains valid.

## Affected Users

- Backend engineers wiring M1.1–M1.7.
- Frontend engineers consuming M1.8 responses.
- Reviewers checking contract drift.

## Non-Goals

- Product search, normalization, ranking, graph execution, provider calls, or UI implementation.
- Adding transient workflow fields to the public `AdvisorState`.
- Defining production ranking weights.
