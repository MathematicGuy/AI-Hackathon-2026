# Design

## Placement

- `backend/app/domain/air_conditioner/hard_constraints.py` — pure, deterministic
  filter logic. No I/O, no randomness, no model calls.
- Reuse the frozen `FilterResult`, `ExcludedProduct`, `NormalizedAirConditioner`,
  and `AirConditionerNeed` contracts from `backend/app/contracts/schemas.py`.
  This story implements against those shapes; it does not redefine them.
- Input container is the US-107 `NormalizedProduct`
  (`backend/app/domain/air_conditioner/evidence.py`), carrying `product`,
  `evidence`, and `missing_fields`.

## Contract of the filter

```python
def filter_products(
    products: list[NormalizedProduct],
    need: AirConditionerNeed,
) -> FilterResult
```

- Deterministic and order-preserving: `eligible_products` and
  `excluded_products` keep the input order.
- A product is eligible iff it violates **no** hard constraint. Otherwise it is
  an `ExcludedProduct(product_id, reasons)` listing **every** violated
  constraint (reasons is order-stable, never empty for an excluded product).

## Hard constraints (PRD §4.10, exercised by M1)

Authority: PRD §4.10 "Hard Constraint Filter" (`docs/product/requirements/…-m1-prd.md`),
the air-conditioner contract invariant "Hard constraints execute before ranking
and cannot be overridden by score", and the frozen ranking fixture's
`eligibility` block (`data/aircon-m1-test-data/aircon-m1-ranking-fixture.json`).

1. **Category** — must be máy lạnh. Enforced upstream: every input is already a
   `NormalizedAirConditioner` (US-107 rejects non-`air_conditioner` records), so
   the filter adds no category check (avoids dead code).
2. **Hard budget** — when `need.budget_max_vnd` is set and
   `product.sale_price_vnd` is **known**, exclude if
   `sale_price_vnd > budget_max_vnd`.
   Reason: `sale_price_vnd {price} exceeds budget_max_vnd {budget}`.
3. **Room fit** — when `need.room_size_m2` is set, compare each known bound
   independently: exclude below a known minimum or above a known maximum;
   inclusive boundary values pass. An unknown bound cannot establish a
   violation. Reasons: `room_size_m2 {room} below recommended_room_area_min_m2
   {min}` or `room_size_m2 {room} above recommended_room_area_max_m2 {max}`.
4. **Stock policy** — the fixture selects `available`, so only the known value
   `"available"` passes. `"unavailable"` and `"unknown"` fail the selected
   policy. Reasons: `stock_status is unavailable` or `stock_status unknown does
   not satisfy stock_policy available`.
5. **Required evidence for the primary priority** — for each priority in
   `need.priorities` with `importance == "primary"` that appears in the fixture
   map, exclude if the required field is missing (unknown). Map (from the
   fixture `eligibility.required_evidence`):
   - `energy_saving` → requires `cspf`
   - `low_noise` → requires `indoor_noise_min_db`
   Reason: `missing required evidence '{field}' for primary priority '{priority}'`.

## Unknown / null field decision (required by the handoff)

**A `null` normalized field (present in `missing_fields`) is UNKNOWN, not a
constraint violation by itself.** A product is excluded when a known value
violates a hard constraint, or when a selected policy requires a known value and
the value is missing. Therefore required primary evidence and the available-only
stock policy fail closed, while unknown price or room bounds remain eligible on
those dimensions.

Citations:
- PRD §10.7 "Missing product evidence": "preserve the product only if missing
  data does not invalidate eligibility; … disclose the missing field; do not
  make claims based on that field."
- PRD §4.10: "required evidence must be present"; "A high score cannot override a
  failed hard constraint."
- Contract invariant: "Unknown product values remain null; malformed values are
  rejected, not guessed."

Golden-case validation of the decision:
- `AC-M1-008` is missing `indoor_noise_min_db`, but `low_noise` is the
  **secondary** priority, so constraint 5 does not apply → **eligible**.
- `AC-M1-009` is missing `cspf` while `energy_saving` is the **primary**
  priority → **excluded** (constraint 5).
- `AC-M1-014` has `stock_status == "unknown"`; it is excluded for **budget**
  (21.5M > 20M) and the available-only stock policy.

## Evidence grounding

`ExcludedProduct` carries only `product_id` and `reasons: list[str]` (frozen), so
grounding is expressed by citing the offending normalized field and its value in
the reason string. Those fields are the same ones US-107 attached an
`EvidenceRef` to, so each known-value reason references an evidence-backed
value; policy-failure reasons cite the normalized field and, for missing values,
the absence disclosed in `missing_fields`. Tests must assert these mappings.
The filter never invents a value to justify an exclusion.

## "Field is known" test

A field is treated as known iff its value on the `NormalizedAirConditioner` is
not `None`. For required-evidence, the field is "substantiated" iff it is not in
`missing_fields` (equivalently, its value is not `None` and US-107 attached an
`EvidenceRef`). No new evidence is synthesized.

## Determinism

No I/O, no randomness, no model calls. Same `(products, need)` in → same
`FilterResult` out. The golden eligible/excluded split for `AIRCON-M1-001` is the
oracle; per-constraint unit cases cover budget, room fit, stock, required
evidence, and the unknown-field branches.
