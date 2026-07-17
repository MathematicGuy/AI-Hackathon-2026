# Validation

## Proof Strategy

Use temporary dotenv files and sentinel model values. Clear canonical process variables in tests so the developer's real `.env` is never read. Prove loading, precedence, sanitization, route order, duplicate rejection, and contract separation without a live provider.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Dotenv load, environment override, explicit env path, missing/blank fields, invalid provider/URL, secret redaction, route order, immutability, duplicate rejection |
| Integration | Configuration bootstrap using an isolated complete dotenv file |
| E2E | Not applicable; no executable gateway or user-visible behavior |
| Platform | Windows-safe root `.env` migration and scoped variable-name verification |
| Performance | Not applicable; settings construct once before runtime composition |
| Logs/Audit | Errors contain canonical variable names only; no secret or raw dotenv values |

## Fixtures

- Temporary dotenv files with sentinel provider, model, URL, and credential values.
- No production credentials or production model identifiers.

## Commands

```powershell
rtk pytest backend/tests/unit/config/test_model_settings.py -q
rtk pytest backend/tests/unit/models/test_routing.py -q
rtk pytest backend/tests/contract/test_m1_contracts.py -q
rtk pytest backend/tests/unit/config/test_model_settings.py backend/tests/unit/models/test_routing.py backend/tests/contract -q
rtk pytest backend/tests -q
rtk git diff --check
```

## Acceptance Evidence

Pending execution. Record exact test counts, configuration-scan result, review verdicts, and Harness trace ID before completing US-122.
