# US-116 — Langfuse Agent Observability

## Current Behavior

`POST /api/v1/agent/respond` executes the agent through `run_turn` and its
injected extractor, polisher, guardrails, state, catalog, ranking, response,
and validation helpers. The accepted M1 contract names a Langfuse trace tree,
but the current backend does not emit that tree or provider-level observations.

## Target Behavior

Every agent turn emits one `advisor_turn` Langfuse trace with the complete
canonical child-observation tree and nested provider generations. Every
short-circuit, fallback, error, and successful response closes its relevant
observation. Tracing is fail-open: missing configuration or Langfuse failures
never change the agent response or deterministic fallback behavior.

## Affected Users

- Customers receiving agent responses; their response path must remain
  available when observability is unavailable.
- Engineers evaluating M1 behavior; they need complete raw inputs, outputs,
  intermediate results, route metadata, and failure evidence per turn.
- Operators configuring model and Langfuse environment settings.

## Affected Product Docs

- `docs/product/air-conditioner-advisor-m1-contract.md`
- `docs/product/architecture/air-conditioner-advisor-m1.md`
- `docs/decisions/0009-m1-explanation-model-routing.md`
- `docs/TRACE_SPEC.md`

## Non-Goals

- Changing model routing order, provider selection, ranking ownership, or
  response schemas.
- Adding Langfuse datasets, judge scoring, dashboards, or release-gate logic.
- Replacing the existing in-memory session store or LangGraph state contract.
- Automatic tracing of every private helper function outside the canonical
  product-level observations.
