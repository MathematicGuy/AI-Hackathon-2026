# US-116 — Langfuse Agent Observability

## Current Behavior

The accepted M1 contract names a complete Langfuse trace tree. The current M1
rig implements only input guard, intent/extraction, and state-merge nodes under
`backend/app/graph/`; it has no complete workflow/API composition root yet.
Those implemented nodes emit no Langfuse observations.

## Target Behavior

Implemented high-value M1 nodes emit canonical child observations when executed
inside an `advisor_turn` context. Missing future nodes are never represented by
fake spans, and low-value helpers do not need individual observations. The
shared adapter comes from US-207. Tracing remains fail-open.

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
- Tracing every private helper or completing the full future canonical tree in
  this story.

## Ownership Dependency

The selected M1 node files previously overlapped USER1/USER2 tracker
boundaries. The integration controller has resolved that overlap and published
Đinh Nhật Thành as sole owner, so implementation may proceed under US-116.
- Implementing missing M1 workflow nodes or a gateway solely to manufacture a
  complete trace tree.
