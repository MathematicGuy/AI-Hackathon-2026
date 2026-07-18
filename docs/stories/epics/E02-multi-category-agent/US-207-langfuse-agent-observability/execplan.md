# E02 Langfuse Agent Observability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Emit one concise, fail-open Langfuse trace for every E02 turn, optimized for bug diagnosis and model improvement.

**Architecture:** Add one SDK-owning adapter under `backend/app/observability/`. Instrument only priority decision boundaries: root request/output, guardrail, understanding/model attempts, state update, route, retrieval, filter/ranking summary, response generation, validation, and final state.

**Tech Stack:** Python 3.12, Langfuse Python SDK 3.15.0, FastAPI, Pydantic 2, pytest 9, pytest-asyncio 1.3.

## Global Constraints

- Capture full raw user/model inputs and outputs.
- Never capture API keys, authorization headers, credentials, or secret environment values.
- Trace failures fail open and never alter response/status/fallback behavior.
- Summarize deterministic work at decision boundaries; do not trace every helper.
- Do not sample E02 turns.
- Preserve `langfuse>=3,<4`; lock remains `3.15.0`.
- Worktree: `.worktrees/observation`; branch: `observation`; base: `main`.

## File Structure

- Create `backend/app/observability/__init__.py`: observer protocol/factories.
- Create `backend/app/observability/langfuse.py`: Langfuse/no-op adapters and nesting.
- Create `backend/tests/unit/observability/test_langfuse.py`: adapter fail-open tests.
- Create `backend/tests/unit/agent/test_observation_api.py`: correlation/root tests.
- Create `backend/tests/unit/agent/test_observation_paths.py`: priority-path tests.
- Create `backend/tests/unit/agent/test_observation_llm.py`: raw model-attempt tests.
- Modify `backend/app/agent/api.py`, `graph.py`, `llm/client.py`, and `demo.py`.
- Modify `.env.example` with safe non-secret tracing settings.

---

### Task 1: Shared Fail-Open Adapter

**Files:**
- Create: `backend/app/observability/__init__.py`
- Create: `backend/app/observability/langfuse.py`
- Test: `backend/tests/unit/observability/test_langfuse.py`

**Interfaces:**
- Produces: `AgentObserver`, `ObservationHandle`, `TurnObservation`, `default_agent_observer()`, `noop_agent_observer()`.

- [ ] **Step 1: Write failing lifecycle tests**

```python
def test_nested_priority_observation_closes_under_root():
    observer = recording_observer()
    with observer.start_turn(
        trace_id="a" * 32,
        session_id="session-1",
        request_id="request-1",
        user_id=None,
        input={"message": "hello"},
        metadata={"environment": "test"},
    ):
        with observer.span("input_guardrail", input={"message": "hello"}) as span:
            span.update(output={"blocked": False})
    assert observer.names == ["agent_turn", "input_guardrail"]
    assert observer.all_ended


def test_sdk_and_flush_failures_never_escape():
    observer = LangfuseAgentObserver(RaisingLangfuse())
    with observer.start_turn(
        trace_id="b" * 32,
        session_id="session-1",
        request_id="request-1",
        user_id=None,
        input={},
        metadata={},
    ) as turn:
        pass
    observer.flush()
    assert turn.observability_degraded is True
```

- [ ] **Step 2: Run RED**

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; rtk proxy uv run pytest -p no:cacheprovider backend/tests/unit/observability/test_langfuse.py -q
```

Expected: FAIL because module does not exist.

- [ ] **Step 3: Implement stable protocol and adapters**

```python
class AgentObserver(Protocol):
    def start_turn(
        self,
        *,
        trace_id: str,
        session_id: str,
        request_id: str,
        user_id: str | None,
        input: object,
        metadata: dict[str, object],
    ) -> ContextManager[TurnObservation]: ...

    def span(
        self,
        name: str,
        *,
        input: object,
        metadata: dict[str, object] | None = None,
        kind: Literal["span", "generation"] = "span",
        model: str | None = None,
        model_parameters: dict[str, object] | None = None,
    ) -> ContextManager[ObservationHandle]: ...

    def flush(self) -> None: ...
```

Use Langfuse `start_observation(..., trace_context={"trace_id": trace_id})`,
child `start_observation`, `update`, `end`, and `flush`. Use `ContextVar` for
async parentage. Catch SDK/serialization errors inside adapter. Missing keys or
disabled tracing returns no-op adapter.

- [ ] **Step 4: Run GREEN and commit**

```powershell
rtk git add backend/app/observability backend/tests/unit/observability/test_langfuse.py
rtk git commit -m "feat: add fail-open Langfuse observer"
```

---

### Task 2: Root Trace and API Correlation

**Files:**
- Modify: `backend/app/agent/api.py`
- Modify: `backend/app/agent/graph.py`
- Modify: `backend/app/agent/demo.py`
- Test: `backend/tests/unit/agent/test_observation_api.py`

**Interfaces:**
- Produces: optional `AgentDependencies.observer`; accepted `AgentResponse.trace_id`; one `agent_turn` per request.

- [ ] **Step 1: Write failing correlation and flush tests**

```python
assert body["trace_id"] == recorder.turns[0].trace_id
assert body["session_id"] == recorder.turns[0].session_id
assert body["request_id"] == recorder.turns[0].request_id
assert recorder.flush_calls == 1
```

Also assert flush failure still returns HTTP 200 and unchanged agent body.

- [ ] **Step 2: Run RED**

Expected: response lacks `trace_id`; dependencies lack observer.

- [ ] **Step 3: Wire root lifecycle**

Allocate IDs before `run_turn`:

```python
request_id = f"request-{uuid.uuid4().hex[:12]}"
trace_id = uuid.uuid4().hex
try:
    with deps.observer.start_turn(
        trace_id=trace_id,
        session_id=session_id,
        request_id=request_id,
        user_id=None,
        input={"message": request.message, "state": state},
        metadata={"environment": "hackathon", "turn_number": state.turn_number + 1},
    ) as turn:
        reply = await run_turn(state, request.message, deps)
        turn.update(output={"reply": reply, "state": state})
finally:
    deps.observer.flush()
```

Return same `trace_id`. Demo creates one root per turn and flushes before exit.

- [ ] **Step 4: Run GREEN and commit**

```powershell
rtk git add backend/app/agent/api.py backend/app/agent/graph.py backend/app/agent/demo.py backend/tests/unit/agent/test_observation_api.py
rtk git commit -m "feat: trace E02 agent turn lifecycle"
```

---

### Task 3: Priority Decision Boundaries

**Files:**
- Modify: `backend/app/agent/graph.py`
- Modify: `backend/app/agent/conversation/understand.py`
- Test: `backend/tests/unit/agent/test_observation_paths.py`

**Interfaces:**
- Produces: `input_guardrail`, `understanding`, `understanding_fallback`, `state_update`, `route_decision`, `policy_retrieval`, `product_search`, `filter_and_rank`, `response_generation`, `output_validation`, `final_state`.

- [ ] **Step 1: Write failing priority-tree tests**

Cover normal product, policy, compare, availability, no-match, stop, guardrail,
fallback, and polish-rejected paths. Assert only executed priority boundaries,
not every helper.

- [ ] **Step 2: Run RED**

Expected: root exists; priority children absent.

- [ ] **Step 3: Wrap existing boundaries without reordering logic**

```python
with deps.observer.span("product_search", input=search_args) as span:
    result = search_products(...)
    span.update(output={"items": result.items, "count": len(result.items)})

with deps.observer.span(
    "filter_and_rank",
    input={"items": result.items, "need": need, "roles": roles},
) as span:
    pool = apply_domain_filters(result.items, need)
    suggestions = suggest_products(pool, category_code=category, roles=roles)
    span.update(output={
        "eligible_ids": [p.productidweb for p in pool],
        "winners": suggestions.winners,
        "skipped_roles": suggestions.skipped_roles,
    })
```

Record guard subtype, route/branch, clarification/no-match/compare/availability
outcome, response source, polish acceptance, and memory delta as metadata on
priority observations. Do not add separate spans for these helper decisions.

- [ ] **Step 4: Run GREEN and commit**

```powershell
rtk git add backend/app/agent/graph.py backend/app/agent/conversation/understand.py backend/tests/unit/agent/test_observation_paths.py
rtk git commit -m "feat: trace E02 decision boundaries"
```

---

### Task 4: Raw Model Attempts and Final Verification

**Files:**
- Modify: `backend/app/agent/llm/client.py`
- Create: `backend/tests/unit/agent/test_observation_llm.py`
- Modify: `.env.example`
- Modify: `docs/stories/epics/E02-multi-category-agent/US-207-langfuse-agent-observability/validation.md`

**Interfaces:**
- Produces: `understanding_model_call` and `response_polish_model_call` generation per candidate attempt.

- [ ] **Step 1: Write failing generation tests**

Assert full system/user/raw output, candidate index, provider/model/role,
temperature, error/fallback result, and absence of API keys.

- [ ] **Step 2: Instrument each candidate attempt**

```python
with self.observer.span(
    "understanding_model_call",
    kind="generation",
    model=candidate.model,
    model_parameters={"temperature": 0},
    input={"system": system, "user": message},
    metadata={"candidate_index": index, "provider": provider_name(candidate.base_url)},
) as generation:
    raw = await self._call(candidate, system, message)
    generation.update(output=raw)
```

On error, mark generation error then preserve existing candidate fallback.
Polisher uses name `response_polish_model_call` and temperature `0.4`.

- [ ] **Step 3: Run focused and full verification**

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; rtk proxy uv run pytest -p no:cacheprovider backend/tests/unit/observability backend/tests/unit/agent -q
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"; rtk proxy uv run --extra test python -m pytest -p pytest_asyncio.plugin -p no:cacheprovider backend/tests -q
rtk proxy uv lock --check
rtk git diff --check
```

Expected: all pass; lock unchanged; traced/untraced responses equal.

- [ ] **Step 4: Record Harness proof and commit**

```powershell
rtk git add backend/app/agent/llm/client.py backend/tests/unit/agent/test_observation_llm.py .env.example docs/stories/epics/E02-multi-category-agent/US-207-langfuse-agent-observability/validation.md
rtk git commit -m "feat: trace E02 model calls"
```

## Stop Conditions

- Payload contains a credential/header/secret.
- Trace changes agent behavior, latency policy, fallback order, or response.
- Proposed span does not help bug diagnosis or model improvement.
- SDK 4 or a new retention/storage policy becomes necessary.
