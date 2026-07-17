# Validation

## Proof Strategy

Unit proof over the pure merge layer, plus the existing contract suite to
prove the public `AdvisorState` and schemas did not drift. RED must fail
before implementation; GREEN must pass after the minimal change; the full
backend suite must stay green.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Newest explicit value overrides older value; omitted fields preserve state; explicit null preserves current value (non-deletion); explicit priority overrides inferred priority with the same name; pending assumption superseded when its field is explicitly provided; confirmed assumptions survive the merge; `clarification_count` resets on a materially new search and is preserved otherwise; hard-constraint change (budget, room size, location, primary priorities) clears retrieved/eligible/excluded/winners/display/output; `ranking_cursor` and `shown_product_ids` unchanged by merge; non-hard-constraint change leaves derived state intact; `WorkflowState` includes every public `AdvisorState` key. |
| Integration | None (pure functions; integration belongs to US-101/US-105). |
| E2E | None. |
| Platform | None. |
| Performance | None. |
| Logs/Audit | None. |

## Fixtures

Deterministic in-test `AirConditionerNeed`, `IntentOutput`, and `Assumption`
instances built from the frozen contract models; no external files.

## Commands

```text
uv run --python 3.12 --extra test pytest backend/tests/unit/graph/nodes/test_merge_state.py -q
uv run --python 3.12 --extra test pytest backend/tests/unit/graph/nodes/test_merge_state.py backend/tests/contract -q
uv run --python 3.12 --extra test pytest backend/tests -q
```

## Acceptance Evidence

Pending implementation.
