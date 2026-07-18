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
