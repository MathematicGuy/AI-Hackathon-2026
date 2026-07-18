# US-116 — Langfuse Agent Observability Validation

## Proof Strategy

Use deterministic fake observer and provider transports. Assert observation
names, parentage, lifecycle closure, raw payloads, route metadata, and response
equivalence across success, fallback, short-circuit, and tracing-failure paths.
Run focused tests first, then the existing backend suite with third-party
plugin autoload disabled.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Adapter enablement/no-op behavior; nested observation lifecycle; JSON-safe payloads; SDK error isolation; flush error isolation. |
| Unit | Extractor and polisher candidate generations capture role/provider/model, full input/output, and provider errors. |
| Integration | API response creates request/trace context before `run_turn`; session continuity and response fields remain unchanged. |
| Integration | Normal, guardrail, policy, compare, no-match, stop, deterministic fallback, and rejected-polish paths produce expected partial/complete trees. |
| E2E | One synthetic M1 turn can be inspected as one `advisor_turn` with canonical children when credentials are configured. |
| Platform | Missing Langfuse credentials, unreachable endpoint, and failed flush do not fail the API response. |
| Performance | Trace export remains asynchronous and does not alter existing response latency contract beyond configured SDK queue behavior. |
| Logs/Audit | No API keys, authorization headers, or environment secrets appear in captured payloads or session logs. |

## Fixtures

- Synthetic air-conditioner catalog and `AIRCON-M1-001` request/response.
- Fake extractor transport with one successful candidate and one failure chain.
- Fake polisher transport with accepted and grounding-rejected outputs.
- In-memory observer recording parent IDs, lifecycle state, payloads, metadata,
  and flush calls.

## Commands

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; rtk proxy uv run pytest -p no:cacheprovider backend/tests/unit/observability backend/tests/unit/agent backend/tests/contract/test_m1_contracts.py -q
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"; rtk proxy uv run --extra test python -m pytest -p pytest_asyncio.plugin -p no:cacheprovider backend/tests -q
rtk proxy uv lock --check
rtk git diff --check
```

## Acceptance Evidence

Implementation must attach focused test output, full-backend output, lockfile
validation, and a sanitized trace/tree example to the Harness story proof.
