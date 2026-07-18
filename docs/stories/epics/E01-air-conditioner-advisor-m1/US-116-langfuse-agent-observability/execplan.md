# M1 Priority Langfuse Observability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Trace implemented M1 input guard, intent/extraction, and state-merge boundaries with full model I/O and fail-open behavior.

**Architecture:** Reuse US-207's shared observer. Inject it optionally into the three implemented M1 nodes and `OpenAIIntentExtractor`; direct calls default to no-op. Do not add a fake gateway, missing graph nodes, or helper-level spans.

**Tech Stack:** Python 3.12, shared Langfuse SDK 3.15.0 adapter, Pydantic 2, pytest 9, pytest-asyncio 1.3.

## Global Constraints

- US-207 shared adapter must be implemented first.
- Full raw model input/output is captured; credentials are excluded.
- Langfuse failures fail open.
- Node return values and M1 contracts remain unchanged.
- Only `input_guardrail`, `intent_classifier`, `intent_model_call`, `deterministic_fallback`, and `state_merge` are in current scope.
- Do not claim the full canonical M1 trace tree.
- Resolve USER1/USER2 ownership overlap before touching selected M1 node files.

## File Structure

- Modify `backend/app/graph/nodes/input_guard.py`.
- Modify `backend/app/graph/nodes/intent.py`.
- Modify `backend/app/graph/nodes/merge_state.py`.
- Modify `backend/app/models/openai_intent.py`.
- Modify focused tests under `backend/tests/unit/graph/nodes/` and `backend/tests/unit/models/`.
- Modify `docs/stories/epics/E01-air-conditioner-advisor-m1/US-116-langfuse-agent-observability/validation.md` with evidence.

---

### Task 1: Priority M1 Node Observations

**Files:**
- Modify: `backend/app/graph/nodes/input_guard.py`
- Modify: `backend/app/graph/nodes/intent.py`
- Modify: `backend/app/graph/nodes/merge_state.py`
- Test: `backend/tests/unit/graph/nodes/test_input_guard.py`
- Test: `backend/tests/unit/graph/nodes/test_intent.py`
- Test: `backend/tests/unit/graph/nodes/test_merge_state.py`

**Interfaces:**
- Consumes: US-207 `AgentObserver` and `noop_agent_observer()`.
- Produces optional `observer: AgentObserver | None = None` keyword on each selected node.

- [ ] **Step 1: Write failing observation tests**

```python
def test_input_guard_records_raw_message_and_result(base_state, recording_observer):
    result = input_guard_node(base_state, observer=recording_observer)
    span = recording_observer.only("input_guardrail")
    assert span.input["message"] == base_state["messages"][-1]
    assert span.output["guardrail_flags"] == result["guardrail_flags"]


@pytest.mark.asyncio
async def test_intent_records_fallback_without_changing_output(recording_observer):
    output, flags = await classify_and_extract(
        "máy lạnh giá bao nhiêu",
        extractor=FailingExtractor(),
        observer=recording_observer,
    )
    assert output.intent == "new_search"
    assert flags == ["intent_model_degraded"]
    assert recording_observer.names == ["intent_classifier", "deterministic_fallback"]


def test_state_merge_records_before_and_after(base_state, recording_observer):
    result = merge_state(base_state, observer=recording_observer)
    span = recording_observer.only("state_merge")
    assert span.input["state"] == base_state
    assert span.output["state"] == result
```

- [ ] **Step 2: Run RED**

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; rtk proxy uv run pytest -p no:cacheprovider backend/tests/unit/graph/nodes/test_input_guard.py backend/tests/unit/graph/nodes/test_intent.py backend/tests/unit/graph/nodes/test_merge_state.py -q
```

Expected: node functions reject `observer`.

- [ ] **Step 3: Wrap node bodies without changing logic**

```python
selected_observer = observer or noop_agent_observer()
with selected_observer.span(
    "input_guardrail",
    input={"message": _latest_message(state), "state": state},
) as observation:
    result = evaluate_input(...)
    new_state = existing_state_update_logic(...)
    observation.update(output={"result": result, "state": new_state})
    return new_state
```

Use same pattern for `intent_classifier` and `state_merge`. On fallback, nest
`deterministic_fallback` under `intent_classifier` and record fallback reason.

- [ ] **Step 4: Run GREEN and commit**

```powershell
rtk git add backend/app/graph/nodes/input_guard.py backend/app/graph/nodes/intent.py backend/app/graph/nodes/merge_state.py backend/tests/unit/graph/nodes
rtk git commit -m "feat: trace M1 priority graph nodes"
```

---

### Task 2: M1 Intent Provider Generation and Proof

**Files:**
- Modify: `backend/app/models/openai_intent.py`
- Test: `backend/tests/unit/models/test_openai_intent.py`
- Modify: `docs/stories/epics/E01-air-conditioner-advisor-m1/US-116-langfuse-agent-observability/validation.md`

**Interfaces:**
- `OpenAIIntentExtractor(..., observer: AgentObserver | None = None)`.
- Produces one `intent_model_call` generation per provider/parse attempt.

- [ ] **Step 1: Write failing raw generation tests**

```python
extractor = OpenAIIntentExtractor(
    fake_client,
    model="configured-model",
    observer=recording_observer,
)
result = await extractor.extract("máy lạnh phòng 18m2")
generation = recording_observer.only("intent_model_call")
assert generation.input == {
    "model": "configured-model",
    "message": "máy lạnh phòng 18m2",
}
assert generation.output == fake_client.raw_response
assert result.intent == "new_search"
assert "api_key" not in repr(generation)
```

Add provider error and schema retry tests. Each attempt ends with output or
error status; existing `ProviderError`/`ValidationError` behavior remains.

- [ ] **Step 2: Instrument attempt loop**

```python
with self.observer.span(
    "intent_model_call",
    kind="generation",
    model=self.model,
    input={"model": self.model, "message": message},
    metadata={"attempt": attempt + 1, "role": "main"},
) as generation:
    raw = await self.client.complete(model=self.model, message=message)
    generation.update(output=raw)
```

On transport/schema failure, mark error then preserve retry/fallback policy.

- [ ] **Step 3: Run focused and full verification**

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; rtk proxy uv run pytest -p no:cacheprovider backend/tests/unit/graph/nodes backend/tests/unit/models/test_openai_intent.py backend/tests/contract/test_m1_contracts.py -q
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"; rtk proxy uv run --extra test python -m pytest -p pytest_asyncio.plugin -p no:cacheprovider backend/tests -q
rtk proxy uv lock --check
rtk git diff --check
```

Expected: all pass; no contract/output change.

- [ ] **Step 4: Record Harness proof and commit**

```powershell
rtk git add backend/app/models/openai_intent.py backend/tests/unit/models/test_openai_intent.py docs/stories/epics/E01-air-conditioner-advisor-m1/US-116-langfuse-agent-observability/validation.md
rtk git commit -m "feat: trace M1 intent model calls"
```

## Stop Conditions

- US-207 adapter is unavailable or incompatible.
- USER1/USER2 ownership overlap remains unresolved.
- A trace payload contains credentials/secrets.
- Observation wiring changes node output, retry, or fallback behavior.
- Work expands into unimplemented M1 workflow nodes or full-tree completion.
