# Overview

## Current Behavior

The frozen public `AdvisorState` contract exists in
`backend/app/contracts/schemas.py` with contract-test coverage, and
`state_merge` exists only as a canonical node name in
`backend/app/graph/node_names.py`. No workflow state module, no merge node,
and no merge tests exist. Multi-turn corrections, assumption transitions, and
ranking invalidation are specified in the accepted authority but not
implemented.

## Target Behavior

A pure, deterministic state-merge layer exists:

- `backend/app/graph/state.py` defines an internal `WorkflowState` that
  extends the frozen public `AdvisorState` with optional transient keys
  (`latest_intent_output`, `raw_products`, `normalized_products`,
  `evidence_by_product`, `display_selections`, `memory_flags`).
- `backend/app/graph/nodes/merge_state.py` merges the validated
  `IntentOutput.need_patch` into the current customer need under the accepted
  precedence chain, preserves omitted fields, treats explicit null as
  non-deletion, supersedes pending assumptions on explicitly provided fields,
  resets `clarification_count` on a materially new search, and invalidates
  derived retrieval/eligibility/ranking/display/output state when a hard
  constraint changes — without touching `ranking_cursor` or
  `shown_product_ids`.

The public `AdvisorState` shape does not drift; existing contract tests stay
green.

## Affected Users

- End customers (multi-turn correction accuracy).
- USER2 lane owner (Lưu Thiện Việt Cường) and the M1.5 integrators who consume
  the merge node.

## Affected Product Docs

- `docs/product/air-conditioner-advisor-m1-contract.md` (State and product
  invariants; canonical graph order).
- `docs/product/requirements/air-conditioner-advisor-m1-prd.md` §4.4, §5.
- `docs/product/architecture/air-conditioner-advisor-m1.md` §6.3, §10.1.

## Non-Goals

- US-105 clarification/routing/persistence behavior.
- Any UI, SQLite, checkpointer, or LLM-call behavior.
- Changing the frozen public `AdvisorState`, enums, or graph order.
- Deletion semantics for explicit null (deferred to a future explicit removal
  intent).
