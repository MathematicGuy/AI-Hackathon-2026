# US-122 Environment-Driven Model Routing

## Current Behavior

Runtime model selections are constants in the public contract module. Intent and extraction share one code-owned selection, the fallback and judge roles have no code configuration boundary, and the existing `.env` model values are not loaded by application code.

## Target Behavior

A typed settings boundary loads required role, provider, base URL, and credential values from `.env` or process environment. Intent and explanation use the main route, extraction uses its separate route, main and extraction failures use the fallback route, and judge evaluation fails closed. Missing configuration fails before runtime composition.

## Affected Users

- Runtime operators configuring provider access.
- Backend engineers implementing M1 model adapters and the gateway.
- Evaluation engineers running model-based judges.
- Reviewers verifying that plans and contracts do not freeze model identifiers.

## Affected Product Docs

- `docs/superpowers/specs/2026-07-18-env-model-routing-design.md`
- `docs/decisions/0009-m1-explanation-model-routing.md`
- `docs/product/architecture/air-conditioner-advisor-m1.md`
- `docs/product/air-conditioner-advisor-m1-contract.md`
- `docs/superpowers/plans/2026-07-17-m1-1-through-m1-8.md`

## Non-Goals

- Calling a live provider.
- Implementing prompts or response generation.
- Creating the future FastAPI gateway or LangGraph workflow.
- Changing deterministic filtering, ranking, role truth, or frontend behavior.
- Storing credentials in tracked files, logs, traces, plans, or specs.
