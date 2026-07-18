# Validation

## Proof Strategy

Contract tests must reject enum, model, graph-order, guardrail-order, envelope,
fixture-count, intent-coverage, golden-winner, or serialization drift.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Pydantic schema validation, enums, graph and guardrail order |
| Integration | Committed catalog/JSONL/manifest/ranking-fixture integrity |
| E2E | Not applicable to M1.0 |
| Platform | Python 3.11+ import and pytest execution |
| Performance | Not applicable to M1.0 |
| Logs/Audit | Story verification and Harness trace |

## Fixtures

- 14-product synthetic catalog.
- 26-case JSONL evaluation dataset.
- Validation manifest and test-only ranking fixture.
- One renderable recommendation response.
- Ten contract smoke scenarios.

## Commands

```powershell
python -m pytest backend/tests/contract -q
.scriptsinharness-cli.exe story verify US-100
```

## Acceptance Evidence

- RED: `python -m pytest backend/tests/contract -vv` collected the contract
  test and failed with `ModuleNotFoundError: No module named 'backend.app'`.
- GREEN: `python -m pytest backend/tests/contract -q` passed 7 tests.
- Harness: `harness-cli story verify US-100` reran the same proof and passed.
- The proof validates 14 synthetic catalog products, 26 JSONL cases, complete
  eight-intent coverage, a passing validation manifest, and the approved
  `AIRCON-M1-001` role winners.
