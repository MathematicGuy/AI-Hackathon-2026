# Validation

## Required Cases

- Every M1 catalog record normalizes to exactly its committed
  `normalized_fixture` (all 14 products).
- Each populated normalized field has an `EvidenceRef` whose `source_snapshot`
  equals the record snapshot and whose `path` is a `$`-rooted JSONPath.
- Absent source fields normalize to `null` and appear in `missing_fields` with
  no evidence entry.
- Malformed numeric (e.g. `"abc BTU"`) raises `ValueError`.
- Wrong category raises `ValueError`.
- Missing required identity or `source_snapshot` raises `ValueError`.
- `normalize_catalog` rejects a page whose records disagree on
  `source_snapshot`.
- Output validates against the frozen `NormalizedAirConditioner` contract.

## Proof status

`scripts/bin/harness-cli story update --id US-107 --unit 1 --integration 0 --e2e 0 --platform 0`

| Layer | Expected proof |
| --- | --- |
| Unit | Normalization, evidence, null-preservation, and rejection tests pass. |
| Integration | Deferred to US-108+ pipeline wiring. |
| E2E | Deferred to M1.5 vertical slice. |
| Platform | N/A. |
| Release | Covered by M1.9 dataset regression. |

## Commands

```powershell
python -m pytest backend/tests/unit/domain/air_conditioner/test_normalization.py -q
python -m pytest backend/tests/unit/domain/air_conditioner/test_normalization.py backend/tests/contract -q
```

## Evidence

Add test output after validation runs.
