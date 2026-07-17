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

- 2026-07-18 RED: 17 failed (modules absent) via
  `uv run --python 3.12 --extra test pytest backend/tests/unit/graph/nodes/test_merge_state.py -q`.
- 2026-07-18 GREEN: 25 passed (17 merge + 8 contract) via the story verify
  command; full backend suite 70 passed (53 pre-existing + 17 new).
- Independent diff review: one doc–code drift (clarification reset wording)
  fixed in `design.md`; one accepted limitation (`requested_product_count`
  reverts to the contract default when unstated) documented in `design.md`.
- `backend/app/graph/nodes/__init__.py` was created as a required package
  marker; it is outside the three owned story files and is flagged to the
  integration controller for ownership assignment.
