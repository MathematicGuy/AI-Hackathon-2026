# Design

## Domain Model

- `WorkflowState(AdvisorState, total=False)`: internal TypedDict extension.
  Transient optional keys owned by later nodes but declared here:
  `latest_intent_output: IntentOutput`, `raw_products: list[dict]`,
  `normalized_products: list[NormalizedAirConditioner]`,
  `evidence_by_product: dict[str, list[EvidenceRef]]`,
  `display_selections: list[str]`, `memory_flags: list[str]`.
  The public `AdvisorState` remains the frozen persistence/contract boundary;
  transient keys never enter the public contract (US-121 design decision).
- `merge_customer_need(current: AirConditionerNeed, intent_output: IntentOutput)
  -> AirConditionerNeed`: pure function. Field-level rules:
  - A field explicitly set on `need_patch` (present in
    `need_patch.model_fields_set`) overrides the current value.
  - An omitted field preserves the current value.
  - An explicitly set `None` is recorded as an explicit statement but does
    **not** delete the current value in M1 (deletion requires a future
    explicit removal intent) — the current value is preserved.
  - Priorities: explicit entries override inferred entries with the same
    `name`; the patched priority list replaces the current list only when the
    patch explicitly sets `priorities`, merged so that current explicit
    entries survive unless the patch explicitly restates them
    (`NeedPriority.source` is the provenance signal).
  - Scalars in `need_patch` are treated as explicit user statements: the
    extraction rules already forbid the intent model from inferring numeric
    values.

## Application Flow

`merge_state(state: WorkflowState) -> WorkflowState` (pure, no I/O):

1. Read `latest_intent_output` (validated upstream by the intent node).
2. Merge the customer need under the precedence chain
   `newest explicit correction > newest explicit statement > previously
   confirmed state > previously inferred assumption > default`.
3. Supersede any pending assumption whose `field` was explicitly provided in
   the patch; keep `confirmed_assumptions` intact across turns.
4. Detect a hard-constraint change: `budget_max_vnd`, `room_size_m2`,
   `location`, or a change to the set of primary-importance priorities.
5. On a hard-constraint change, clear `retrieved_product_ids`,
   `eligible_product_ids`, `excluded_products`, `role_winners`,
   `display_product_ids`, and `recommendation_output`. Never modify
   `ranking_cursor` or `shown_product_ids` during merge (cursor advances only
   after successful presentation; shown IDs feed show-more exclusions).
6. Reset `clarification_count` to 0 when the turn starts a materially new
   search (`new_search` intent whose patch explicitly changes a core need
   field); otherwise preserve it.
7. Set `current_intent`, increment `turn_number`, and update
   `requested_product_count` from the intent output.

## Interface Contract

- Inputs/outputs use only frozen contract types from
  `backend/app/contracts/schemas.py` (`AirConditionerNeed`, `IntentOutput`,
  `Assumption`, `ExcludedProduct`, `RoleWinners`, `RecommendationOutput`).
- No new public API surface. `WorkflowState` is internal to
  `backend/app/graph/`.

## Data Model

None. No persistence, schema, or migration changes. The LangGraph
checkpointer (US-105) later persists the public fields only.

## UI / Platform Impact

None.

## Observability

None in this story; the `state_merge` span is emitted by the workflow
integration story (US-101/US-116). The merge function stays pure to keep that
span trivial to wrap.

## Alternatives Considered

1. Mutating merge inside the graph node with direct state writes — rejected:
   harder to test, violates the pure-domain proof expectation.
2. Treating explicit null as deletion — rejected: the frozen tracker
   constraint says explicit null is not deletion in M1.
3. Extending public `AdvisorState` with transient fields — rejected: US-121
   froze the public shape; transient keys belong to the internal
   `WorkflowState`.
