# Execution Plan

## Dependency

- Depends on US-107 (product normalization + evidence). The filter consumes the
  US-107 `NormalizedProduct` output and the frozen contracts; no upstream change
  is required.
- Unblocks US-109 (injected deterministic ranking), which consumes
  `FilterResult.eligible_products`.

## TDD RED → GREEN

1. **RED — write `backend/tests/unit/domain/air_conditioner/test_hard_constraints.py`.**
   - Golden oracle: load `data/aircon-m1-test-data/aircon-m1-catalog-enriched.json`,
     `normalize_catalog(...)`, build the `AIRCON-M1-001` need (budget 20,000,000,
     room 18, priorities energy_saving=primary, low_noise=secondary), call
     `filter_products`, and assert:
     - eligible ids == `[AC-M1-001 … AC-M1-008]` (input order)
     - excluded ids == `[AC-M1-009 … AC-M1-014]` (input order)
     - each `ExcludedProduct.reasons` cites the expected constraint (budget,
       room fit, stock, or missing primary evidence).
   - Per-constraint unit cases (small hand-built `NormalizedProduct` inputs):
     budget over/at/under; room below/within/above range; stock
     available/unavailable/unknown; primary-evidence present/missing;
     secondary-evidence missing (must stay eligible); multiple simultaneous
     violations accumulate all reasons; unknown price / unknown area preserve
     the product.
   - Run: expect failures (module absent).
2. **GREEN — implement `backend/app/domain/air_conditioner/hard_constraints.py`.**
   - `filter_products(products, need) -> FilterResult` per design.md.
   - Module constant `_REQUIRED_EVIDENCE_BY_PRIMARY = {"energy_saving": ("cspf",),
     "low_noise": ("indoor_noise_min_db",)}` grounded in the fixture
     `eligibility.required_evidence`. No injected-policy framework (that is
     US-109; AGENTS.md forbids single-use abstraction).
   - Order-preserving single pass; accumulate all violated-constraint reasons per
     product.
   - Re-run the test file: expect green.
3. **Full backend suite** — run pytest with
   `PYTHONPATH="E:/VIN-INTERNSHIP/AI-Hackathon-2026"`; confirm no regression
   (US-107 baseline was 166 tests; US-108 adds cases).

## Commands

```powershell
$env:PYTHONPATH="E:/VIN-INTERNSHIP/AI-Hackathon-2026"
pytest backend/tests/unit/domain/air_conditioner/test_hard_constraints.py -q   # iterate
pytest -q                                                                       # final
```

## Closure

- `harness-cli story verify` → record standard-tier Trace (`--read` + `--friction`,
  outcome `completed`) → `harness-cli audit` → `harness-cli propose`.
- Update `docs/team/now/THANH-NOW.md`.
- Finalize the session log.
