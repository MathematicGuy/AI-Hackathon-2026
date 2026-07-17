# Validation

## Proof Strategy

Unit proof over the deterministic guardrail plus the existing contract suite to
prove no public contract drift. RED must fail before implementation; GREEN must
pass after the minimal change; the full backend suite must stay green.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Empty/whitespace blocks; 149 words allowed and 150 blocks with the contract message; Unicode counted correctly; repeated-character abuse blocks; prompt-injection marker blocks; encoded-payload blocks; over-long URL blocks; unsafe-execution and credential/hidden-prompt requests block; unrelated category and auto-purchase mark `unsupported`; valid máy lạnh request passes; stage order short-circuits (an earlier blocking stage wins over a later one); NeMo blocks when available-and-disallowed; NeMo unavailable continues only for low-risk in-scope and fails closed otherwise with `guardrail_degraded`; node writes `guardrail_flags` and a block marker. |
| Integration | None (pure/injected; wiring is US-101). |
| E2E | None. |
| Platform | None. |
| Performance | None. |
| Logs/Audit | `guardrail_flags` reflect degradation; span emission is US-101. |

## Fixtures

In-test message strings and a fake `NemoInputRail` (allow / disallow /
unavailable). No external files or network.

## Commands

```text
uv run --python 3.12 --extra test pytest backend/tests/unit/guardrails backend/tests/unit/graph/nodes/test_input_guard.py -q
uv run --python 3.12 --extra test pytest backend/tests/unit/guardrails backend/tests/unit/graph/nodes/test_input_guard.py backend/tests/contract -q
uv run --python 3.12 --extra test pytest backend/tests -q
```

## Acceptance Evidence

Pending implementation.
