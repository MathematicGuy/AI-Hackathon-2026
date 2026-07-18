# US-116 — Langfuse Agent Observability Validation

## Proof Strategy

Use the US-207 in-memory observer and fake provider transports. Assert priority
names, parentage, lifecycle closure, raw payloads, route metadata, and node
output equivalence for input guard, intent/extraction, and state merge. Do not
claim complete-tree coverage.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Adapter enablement/no-op behavior; nested observation lifecycle; JSON-safe payloads; SDK error isolation; flush error isolation. |
| Unit | Extractor and polisher candidate generations capture role/provider/model, full input/output, and provider errors. |
| Integration | `input_guardrail`, `intent_classifier`, and `state_merge` nest under an injected `advisor_turn`. |
| Contract | Existing M1 request/state contracts remain unchanged by observation wiring. |
| E2E | Deferred until an M1 workflow composition root exists; no fake gateway is added by this story. |
| Platform | Missing Langfuse credentials, unreachable endpoint, and failed flush do not fail the API response. |
| Performance | Trace export remains asynchronous and does not alter existing response latency contract beyond configured SDK queue behavior. |
| Logs/Audit | No API keys, authorization headers, or environment secrets appear in captured payloads or session logs. |

## Fixtures

- Synthetic air-conditioner state/request fixtures from existing node tests.
- Fake extractor transport with one successful candidate and one failure chain.
- In-memory observer recording parent IDs, lifecycle state, payloads, metadata,
  and flush calls.

## Commands

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; rtk proxy uv run pytest -p no:cacheprovider backend/tests/unit/observability backend/tests/unit/graph backend/tests/contract/test_m1_contracts.py -q
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"; rtk proxy uv run --extra test python -m pytest -p pytest_asyncio.plugin -p no:cacheprovider backend/tests -q
rtk proxy uv lock --check
rtk git diff --check
```

## Acceptance Evidence

Implementation must attach focused/full test output, lock validation, and a
sanitized priority tree. Complete-tree evidence is outside this story.
