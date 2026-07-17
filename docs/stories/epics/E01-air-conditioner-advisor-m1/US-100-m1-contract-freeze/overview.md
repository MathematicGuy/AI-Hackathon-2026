# US-100 M1 Contract Freeze

## Current Behavior

The approved workflow and synthetic evaluation fixtures exist, but no active M1
story, importable contract schemas, graph-name constants, mock payload, or
mechanical contract proof exists.

## Target Behavior

M1 request, response, state, product, ranking, evidence, error, graph, model
routing, and fixture contracts are frozen and mechanically verified before
M1.1–M1.4 begin.

## Affected Users

- Engineers implementing M1.1–M1.9.
- Reviewers validating architecture drift and evaluation truth.

## Affected Product Docs

- `docs/product/air-conditioner-advisor-m1-contract.md`
- `WORKFLOW-MVP(4).md`
- `docs/decisions/0009-m1-explanation-model-routing.md`

## Non-Goals

- Catalog adapters, production ranking, guardrail execution, persistence, LLM
  calls, UI, or Langfuse integration.
- Treating synthetic fixture data as live product data.

