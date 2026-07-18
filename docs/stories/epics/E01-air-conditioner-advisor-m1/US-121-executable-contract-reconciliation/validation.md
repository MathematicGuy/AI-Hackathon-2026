# Validation

## Proof Strategy

The contract test must fail before production changes, then pass while the existing M1.0 mock and enum assertions remain green.

## Test Plan

| Layer | Proof |
| --- | --- |
| Contract | Error envelope, display alternative, conditional trace, frozen formal roles |
| Compatibility | Existing request/response fixture and all seven M1.0 tests |
| Dependency | Editable-install resolution dry run |

## Commands

```powershell
python -m pytest backend/tests/contract/test_m1_contracts.py -q
python -m pytest backend/tests/contract -q
python -m pip install -e ".[test]" --dry-run
```

## Acceptance

- RED is captured before schema/constants implementation.
- Contract suite passes after implementation.
- Existing mock response remains serializable.
- Formal roles remain exactly three.
- No production ranking policy is added.
