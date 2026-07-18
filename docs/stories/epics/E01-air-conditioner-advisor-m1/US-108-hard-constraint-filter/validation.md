# Validation

## Success criteria

`filter_products` produces the frozen `FilterResult` for the golden case and each
per-constraint unit case, deterministically and order-preserving, with grounded
exclusion reasons; the full backend suite stays green.

## Golden oracle — `AIRCON-M1-001`

Need: `budget_max_vnd=20000000`, `room_size_m2=18`, priorities
`energy_saving` (primary) + `low_noise` (secondary).

| product | verdict | reason |
|---------|---------|--------|
| AC-M1-001 … AC-M1-007 | eligible | all constraints pass |
| AC-M1-008 | eligible | missing `indoor_noise_min_db`, but `low_noise` is secondary → no required-evidence violation |
| AC-M1-009 | excluded | missing `cspf`, `energy_saving` is primary → required-evidence violation |
| AC-M1-010 | excluded | room 18 outside `[10, 15]` |
| AC-M1-011 | excluded | room 18 outside `[20, 30]` |
| AC-M1-012 | excluded | `stock_status` unavailable |
| AC-M1-013 | excluded | room 18 outside `[20, 30]` |
| AC-M1-014 | excluded | `sale_price_vnd` 21,500,000 > budget 20,000,000; `stock_status` unknown fails available-only policy |

Assertions: `eligible ids == [AC-M1-001..008]`; `excluded ids == [AC-M1-009..014]`;
both lists in input order; each excluded product's `reasons` matches the table.

## Per-constraint unit cases

- **Budget**: price > budget → excluded; price == budget → eligible; price <
  budget → eligible; price unknown (null) → eligible (not a violation).
- **Room fit**: room < known min or > known max → excluded; room == min / ==
  max / within → eligible; an unknown bound cannot exclude on that side.
- **Stock**: `available` → eligible; `unavailable` or `unknown` → excluded by
  the selected available-only policy.
- **Required evidence**: primary `energy_saving` with `cspf` present → eligible;
  primary `energy_saving` with `cspf` missing → excluded; primary `low_noise`
  with `indoor_noise_min_db` missing → excluded; secondary `low_noise` with
  `indoor_noise_min_db` missing → eligible.
- **Accumulation**: a product violating budget AND room fit lists both reasons,
  in constraint order.
- **Determinism / order**: same input twice → identical `FilterResult`; eligible
  and excluded lists preserve input order.
- **Evidence grounding**: known-value and explicit-unknown exclusion reasons
  reference populated fields present in `NormalizedProduct.evidence`; absent
  required fields or absent stock reference fields listed in `missing_fields`.

## Proof commands

```powershell
$env:PYTHONPATH="E:/VIN-INTERNSHIP/AI-Hackathon-2026"
python -m pytest backend/tests/unit/domain/air_conditioner/test_hard_constraints.py -q -p no:cacheprovider
python -m pytest -q -p no:cacheprovider
```

Record the final counts (golden + unit cases pass; full suite green, no
regression) in the session log and the Harness trace.
