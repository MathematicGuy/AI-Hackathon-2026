# US-108 Hard Constraint Filter

## Current Behavior

`normalize_catalog` (US-107) turns raw catalog records into a
`list[NormalizedProduct]` (each carrying `product`, `evidence`,
`missing_fields`). Nothing splits that list into an eligible set and an excluded
set against the customer's hard constraints. The canonical graph step
`product_normalization → hard_constraint_filter → availability_decision`
(air-conditioner contract, "Canonical graph order") has no implementation, so
availability decisioning (US-108 successor work) and deterministic role ranking
(US-109) have no eligible set to consume.

## Target Behavior

Provide a deterministic hard-constraint filter (air-conditioner slice) that
takes the normalized catalog plus the resolved `AirConditionerNeed` and produces
the frozen `FilterResult` contract:

- Split products into `eligible_products` (`list[NormalizedAirConditioner]`) and
  `excluded_products` (`list[ExcludedProduct]`), preserving input order in both.
- Enforce the PRD §4.10 hard constraints that M1 exercises: hard budget, room
  fit, stock policy, and required evidence for the active primary priority.
- Ground every exclusion in the offending normalized field value (which is
  itself evidence-backed); never exclude on a guessed or unknown value.
- Treat a `null`/unknown normalized field as unknown, not a violation unless a
  selected hard policy requires a known value. Thus missing primary-priority
  evidence and an unknown stock value fail their selected policies, while
  unknown price or room bounds do not create guessed violations (PRD §10.7,
  §4.10).
- For the golden case `AIRCON-M1-001` (budget 20,000,000 VND, room 18 m²,
  primary `energy_saving`, secondary `low_noise`), the eligible set is exactly
  `AC-M1-001 … AC-M1-008` and the excluded set is `AC-M1-009 … AC-M1-014`.

## Non-Goals

- Deterministic role ranking, best-value/cheapest scoring, tie-breaking, or the
  injected ranking policy (US-109).
- Truthful deduplication / badge merge (US-110).
- The `availability_decision` node, constraint recovery, graph wiring, or
  provider calls (US-108 successor stories).
- Editing the frozen `FilterResult` / `ExcludedProduct` / `NormalizedAirConditioner`
  contract in `backend/app/contracts/schemas.py`.
- Data-confidence scoring; US-108 only decides eligibility, not rank inputs.
