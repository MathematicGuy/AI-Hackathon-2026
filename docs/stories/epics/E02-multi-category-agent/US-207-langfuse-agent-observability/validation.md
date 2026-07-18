# US-207 — E02 Langfuse Agent Observability Validation

## Proof Strategy

Inject an in-memory observer and fake LLM transports. Compare responses with and
without tracing, then assert priority-boundary parentage, lifecycle closure,
payloads, metadata, errors, and flush behavior.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Real/no-op adapter selection, nesting, JSON serialization, degradation, and flush failure. |
| Unit | Extractor/polisher candidate generations, raw prompts/outputs, provider errors, and fallback order. |
| Unit | `filter_and_rank` summary records selected/skipped roles and winner IDs. |
| Integration | Root correlation and full normal/policy/compare/availability/no-match/stop/guardrail trees. |
| Integration | Tracing-disabled and tracing-failure responses equal uninstrumented behavior. |
| E2E | Sanitized Langfuse project shows one turn under one session with expected hierarchy. |
| Security | No credential value or authorization header appears in captured payloads. |

## Commands

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; rtk proxy uv run pytest -p no:cacheprovider backend/tests/unit/observability backend/tests/unit/agent -q
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"; rtk proxy uv run --extra test python -m pytest -p pytest_asyncio.plugin -p no:cacheprovider backend/tests -q
rtk proxy uv lock --check
rtk git diff --check
```

## Acceptance Evidence

Attach focused/full test results, response-equivalence proof, lock validation,
secret-scan result, and one sanitized exported trace-tree example.

## Task 4 Evidence (2026-07-18)

- Focused generation tests: `backend/tests/unit/agent/test_observation_llm.py` — 3 passed.
- Task 1–3 observer/agent regressions plus Task 4 tests — 43 passed, 1 existing Starlette deprecation warning.
- Full backend suite was attempted with the repository-safe pytest command but timed out after 124 seconds without completing; no failure traceback was emitted.
- `uv lock --check` — passed (`Resolved 72 packages`).
- `git diff --check` — passed.
- Fake transports verified complete system/user prompts, raw outputs, candidate order/index, provider/model/role, temperatures, fallback error metadata, and that API keys never enter captured payloads. Tracing exceptions are fail-open in the LLM client.
- No live Langfuse project or E2E trace was used; sanitized E2E evidence remains pending credentials and environment access.
