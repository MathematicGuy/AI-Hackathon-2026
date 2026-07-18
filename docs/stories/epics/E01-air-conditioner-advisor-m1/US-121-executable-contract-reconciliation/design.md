# Design

## Decisions

- Add `AdvisorError` exactly as accepted in
  `docs/product/architecture/air-conditioner-advisor-m1.md`.
- Add display-only `best_for_primary_priority` through `BadgeKind`; formal `RecommendationRole` remains exactly three values.
- Add optional `selection_reason` to `ProductCard`; existing mock cards remain valid.
- Add `CONDITIONAL_TRACE_NODES = ("constraint_recovery",)` while preserving `CANONICAL_TRACE_NODES` as the common trace tree.
- Keep transient LangGraph data out of public `AdvisorState`; M1.4 will introduce an internal `WorkflowState` extension.
- Add `pyproject.toml` for the framework/provider/test dependency boundary.

## Risks and Controls

- Risk: display badge becomes a fourth role. Control: contract tests keep `RecommendationRole` at exactly three and validate `RoleWinners` unchanged.
- Risk: common trace changes. Control: preserve existing tuple and test recovery separately.
- Risk: dependency drift. Control: bounded major-version ranges and a resolution dry run.
