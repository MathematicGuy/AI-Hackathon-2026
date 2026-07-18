# OBSERVIBILITY-NOW — Langfuse instrumentation map & update procedure

**Scope:** This file is the single source of truth for the *observability layer*
(Langfuse tracing) only. It exists so a future agent that re-syncs the branch
with `main` can update tracing **without re-reading the whole agent codebase**.
Read this first, then read only the files it points at and the code diff from
`main`.

- This file is **independent** of the product-progress trackers. It does NOT
  track task or product progress — it is limited to the observability layer
  (span map, adapter invariants, test contract, and update procedure).
- Owner: dinh-nhat-thanh (see `docs/team/now/README.md`).

**Last synced with `main`:** commit `3068a66` ("Update Hackathon checklist to
git"), 2026-07-19. **Adapter SDK:** `langfuse` 4.x. **Latest live trace:**
`033beedefc9f4d48b4056bc39a8c1bb8` (project `cmrqtlknr008vad0dwhwviuv6`).

---

## 1. Observability tree (state at a glance)

Legend: `[S]` span · `[G]` generation · `(→ file::function)` where it is emitted.
Names are the **stable contract** — dashboards and tests depend on them.

```text
agent_turn [S]                         (→ observability/langfuse.py::LangfuseAgentObserver.start_turn)
│                                        wired by: agent/api.py::respond, agent/demo.py::main
├── input_guardrail [S]                (→ agent/graph.py::_run_turn_core)   # exploit branch + main guard
├── understanding [S]                  (→ agent/conversation/understand.py::understand_turn)
│   ├── understanding_model_call [G]   (→ agent/llm/client.py::LLMUnderstandingExtractor.extract)  # one per candidate/retry
│   └── understanding_fallback [S]     (→ agent/conversation/understand.py::understand_turn)        # only when extractor missing/fails
├── state_update [S]                   (→ agent/graph.py::_run_turn_core)   # before/after snapshot + memory_delta
├── route_decision [S]                 (→ agent/graph.py::_run_turn_core)   # intent → route/branch
├── policy_retrieval [S]               (→ agent/graph.py::_policy_flow)     # policy_question path only
├── product_search [S]                 (→ agent/graph.py::_product_flow)    # product paths only
├── filter_and_rank [S]                (→ agent/graph.py::_product_flow)    # only when search matched
├── response_polish_model_call [G]     (→ agent/llm/client.py::LLMPolisher.polish)  # only when AGENT_LLM_POLISH on
├── response_generation [S]            (→ agent/graph.py::_observed_response)  # EVERY user-facing reply
├── output_validation [S]              (→ agent/graph.py::_observe_output_validation)  # product/policy/compare replies
└── final_state [S]                    (→ agent/graph.py::run_turn, finally)   # always last, fail-open
```

### M1 rig (separate node functions, injected observer, not yet under a live root)

```text
input_guardrail [S]                    (→ graph/nodes/input_guard.py::input_guard_node)
intent_classifier [S]                  (→ graph/nodes/intent.py::classify_and_extract)
├── intent_model_call [G]              (→ models/openai_intent.py::OpenAIIntentExtractor.extract)
└── deterministic_fallback [S]         (→ graph/nodes/intent.py::classify_and_extract)  # on provider/schema failure
state_merge [S]                        (→ graph/nodes/merge_state.py::merge_state)
```

---

## 2. Instrumentation surface (the only files that carry tracing)

Update tracing by editing **only** these. Everything else is agent logic.

| File | Role |
| --- | --- |
| `backend/app/observability/langfuse.py` | Adapter: `AgentObserver` protocol, `LangfuseAgentObserver`, `NoopAgentObserver`, `default_agent_observer()`, `redact_payload`. |
| `backend/app/observability/__init__.py` | Public exports. |
| `backend/app/agent/graph.py` | E02 spans + helpers `_observer`, `_state_snapshot`, `_observed_response`, `_observe_output_validation`; `AgentDependencies.observer`. |
| `backend/app/agent/conversation/understand.py` | `understanding` / `understanding_fallback` spans. |
| `backend/app/agent/llm/client.py` | `understanding_model_call` / `response_polish_model_call` generations; `default_extractor(observer=)`, `default_polisher(observer=)`. |
| `backend/app/agent/api.py` | Root `start_turn` + `flush()` per request. |
| `backend/app/agent/demo.py` | Root `start_turn` + `flush()` per turn. |
| `backend/app/graph/nodes/{input_guard,intent,merge_state}.py` | M1 node spans. |
| `backend/app/models/openai_intent.py` | M1 `intent_model_call` generation. |

---

## 3. Adapter invariants (never break these)

1. **Fail-open.** Any tracing error → silent no-op; agent output is byte-for-byte
   unchanged. Missing `LANGFUSE_*` keys → `NoopAgentObserver`.
2. **No-op default.** Every instrumented function takes `observer` defaulting to
   `noop_agent_observer()`; outputs are identical with and without an observer
   (asserted by tests).
3. **Redaction two-layer** (`redact_payload`): key-based (`_is_secret_key`) +
   env-value substring (`_secret_values`, only values ≥ 8 chars). Never emit API
   keys, auth headers, or secret env values into any payload.
4. **Additive only.** Tracing must never change agent behavior, control flow, or
   response text. If a span would alter behavior, the instrumentation is wrong.

---

## 4. Test contract (authoritative — run these after any change)

- `backend/tests/unit/agent/test_observation_paths.py` — **the span-order
  contract** per route (normal/policy/compare/availability/no-match/stop/guardrail/
  extractor-failure/polish-rejection). This is what "correct instrumentation"
  means.
- `backend/tests/unit/agent/test_observation_llm.py` — generation spans, prompt/
  output capture, provider-error redaction, factory observer injection.
- `backend/tests/unit/agent/test_observation_api.py` — one root turn per request,
  flush once, flush-failure stays HTTP 200.
- `backend/tests/unit/observability/test_langfuse.py` — adapter + redaction.
- `backend/tests/unit/graph/nodes/*`, `backend/tests/unit/models/test_openai_intent.py`
  — M1 node spans.
- `backend/tests/unit/conftest.py` — `RecordingObserver` / `RecordingSpan`
  fixtures (the fake observer used everywhere).

Run (Windows, from worktree root):

```powershell
$env:PYTHONPATH="$PWD"; $env:AGENT_DATA_BACKEND="excel"; $env:OPENAI_API_KEY=""
.venv\Scripts\python.exe -m pytest -p no:cacheprovider `
  backend/tests/unit/agent/test_observation_paths.py `
  backend/tests/unit/agent/test_observation_llm.py `
  backend/tests/unit/agent/test_observation_api.py `
  backend/tests/unit/observability backend/tests/unit/graph backend/tests/unit/models -q
```

> Clear `OPENAI_API_KEY` for the run: `test_refinements.py::test_resolve_candidates_from_minimal_env`
> reads `os.environ` and fails if a real key is present (pre-existing, not
> observability). Exclude the live-Postgres test `integration/api/test_catalog_endpoints.py`.

---

## 5. Update procedure — "main changed the agent, re-instrument"

**Golden rules:** (a) span **names** are frozen unless you also update tests +
this file; (b) instrumentation is additive and fail-open; (c) let the span-order
tests define "done".

### Step 0 — Sync
```
git checkout observation
git merge main --no-ff        # pull newest agent code INTO observation first
```

### Step 1 — Resolve conflicts (agent core: understand.py, graph.py, api.py, llm/client.py)
- **Small conflict** (signature/one block): keep main's logic, re-wrap with the
  span (see `understand.py` for the pattern — main's control flow inside the
  `observer.span("understanding")` context).
- **Large conflict** (graph.py heavily refactored): take main's whole file, then
  re-apply spans:
  ```
  git checkout --theirs backend/app/agent/graph.py
  ```
  Re-add: imports; `AgentDependencies.observer` + `from_default_paths` wiring;
  the 4 helpers (`_observer`, `_state_snapshot`, `_observed_response`,
  `_observe_output_validation`); the `run_turn` try/finally `final_state`
  wrapper; and the per-node spans below.

### Step 2 — Map new/changed agent structure to spans (scenario playbook)

| Scenario in main's diff | Observability action |
| --- | --- |
| New router branch / flow that returns a reply | Wrap the dispatch return in `_observed_response(observer, <flow>(...), outcome="<name>")`. No deep threading needed. |
| Flow renamed/moved | Move its span with it; **keep the span name unchanged**. |
| Flow signature changed (fields referenced by a span) | Update only the span `input`/`output` payload keys; keep the span. |
| A flow now calls an instrumented flow (e.g. `_product_flow`) | Thread `observer` into it so the inner spans still attach. |
| New provider/model call added | Wrap it with a `*_model_call` **generation** using the `_generation_span` pattern in `llm/client.py` (`kind="generation"`, `model`, `model_parameters`, role metadata). |
| Behavior a test asserts changed (e.g. `display_source` text) | Update that **test assertion** to main's new behavior; keep the span-order assertions intact. |
| New early-return gate before understanding | Emit `input_guardrail` (if guard-like) or wrap reply with `_observed_response`; `final_state` still fires via `run_turn` finally. |

### Step 3 — Verify (before AND after must be green)
Run the §4 suite, then the full backend suite with `AGENT_DATA_BACKEND=excel`,
`OPENAI_API_KEY=""`, excluding the live-Postgres endpoint test.

### Step 4 — Live smoke (mandatory before pushing to main)
Set the four `LANGFUSE_*` vars + `AGENT_DATA_BACKEND=excel`, run one turn via
`backend/app/agent/demo.py` (or a one-shot script), `flush()`, then confirm the
trace in Langfuse and that **no secret** appears in any payload
(`langfuse-cli api traces get <id> --fields core,observations`). Record the new
trace ID in §6 and in both `validation.md` files.

### Step 5 — Land
Commit on `observation`, then `git checkout main && git merge observation`
(fast-forward once main is contained), push.

---

## 6. Version / trace log

| Date | Synced main | Trace ID | Notes |
| --- | --- | --- | --- |
| 2026-07-19 | `3068a66` | `033beedefc9f4d48b4056bc39a8c1bb8` | Re-instrumented after main's agent refactor (new intents: smalltalk, product_qa, catalog_overview, price_range_query, promotion_inquiry, question_clarification). Full tree verified. |
| 2026-07-18 | pre-refactor | `9a7e6a4216344b009ac432aac251651e` | New Langfuse project keys. |
| 2026-07-18 | pre-refactor | `704327523e3f427a86c2c2b6e28c27bf` | First live smoke (original project). |
