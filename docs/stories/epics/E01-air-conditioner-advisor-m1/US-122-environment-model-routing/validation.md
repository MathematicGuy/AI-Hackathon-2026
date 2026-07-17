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

### Automated tests

- Focused configuration, routing, and contract suite: `51 passed`, `1 warning`
  in `0.59s`.
- Full backend suite: `96 passed`, `1 warning` in `0.70s`.
- Both runs disabled third-party plugin autoload and used separate
  workspace-local base temporary directories.
- The warning in each run was `PytestConfigWarning: Unknown config option:
  asyncio_mode`; this is environment-only because the plugin that registers
  the option was intentionally not autoloaded.

### Configuration and literal scans

- All twelve canonical local configuration names exist exactly once.
- The legacy configuration name is absent.
- The existing API-key and team-member entries were preserved without exposing
  their values.
- `.env` is ignored, has zero ordinary status entries, and is not staged.
- The scoped customer-runtime scan found zero production model or base-URL
  literals in backend source/tests, the routing plan/spec, the US-122 packet,
  ADR 0009, the product contract, the active M1 plan, or the workflow PRD.
- `ARCHITECTURE.md` has exactly one remaining model literal, in the explicitly
  preserved engineering coding-assistant entry; customer-runtime sections have
  none.

### Diff and scope checks

- `rtk git diff --check` passed with no output before staging.
- Tracked changes are limited to ADR 0009, `ARCHITECTURE.md`,
  `WORKFLOW-MVP(4).md`, the product contract, the active M1 plan, and this
  validation file.
- Cached whitespace and exact staged-scope checks passed before commit.
- `.env`, `THANH-NOW.md`, and unrelated dirty files were not staged.

### Review result

The scoped diff preserves deterministic filtering/ranking, public advisor data
contracts, and frontend behavior. Runtime provider/model swaps are now
operator environment changes; role responsibilities, route order, and failure
policy remain architecture-controlled. No live provider or E2E run was needed
for this documentation/configuration migration.
