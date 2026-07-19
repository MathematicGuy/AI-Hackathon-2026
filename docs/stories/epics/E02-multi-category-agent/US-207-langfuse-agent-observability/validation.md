# US-207 — E02 Langfuse Agent Observability Validation

## Proof Strategy

Inject an in-memory observer and fake LLM transports. Compare responses with and
without tracing, then assert priority-boundary parentage, lifecycle closure,
payloads, metadata, errors, and flush behavior.

Task 4 additionally verifies that `AgentDependencies.from_default_paths()`
injects one observer into both default LLM clients, so generation observations
attach to the active root turn. Raw provider exception text is excluded from
captured error metadata.

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

Final evidence is recorded below. No live Langfuse credentials were available,
so E2E trace-tree evidence is explicitly pending rather than inferred.

## Task 4 Evidence (2026-07-18)

- Focused generation and factory-wiring tests: `backend/tests/unit/agent/test_observation_llm.py` — 4 passed.
- Agent and observability regressions (`backend/tests/unit/agent backend/tests/unit/observability`) — 120 passed, 1 existing Starlette deprecation warning.
- Full backend suite was attempted with the repository-safe pytest command but timed out after 124 seconds without completing; no failure traceback was emitted.
- `uv lock --check` — passed (`Resolved 72 packages`).
- `git diff --check` — passed.
- Fake transports verified complete system/user prompts, raw outputs, candidate order/index, provider/model/role, temperatures, fallback markers, observer injection, and that API keys, authorization material, and raw provider error text never enter captured payloads. Tracing exceptions are fail-open in the LLM client.
- Task 4 scope includes the minimal `backend/app/agent/graph.py` wiring required to pass the active root observer into default extractor/polisher instances.
- No live Langfuse project or E2E trace was used; sanitized E2E evidence remains pending credentials and environment access.

### Live Langfuse smoke trace (2026-07-19)

**Trace ID:** `033beedefc9f4d48b4056bc39a8c1bb8`
**Langfuse URL:** `https://jp.cloud.langfuse.com/project/cmrqtlknr008vad0dwhwviuv6/traces/033beedefc9f4d48b4056bc39a8c1bb8`
**Observer:** `LangfuseAgentObserver` (live, fail-open no-op confirmed inactive)

One agent turn (`tư vấn máy lạnh cho phòng 20m2`) produced a complete trace
with the expected span hierarchy under a single root `agent_turn`. The
`understanding_model_call` GENERATION captured full system/user prompts and
structured output via `deepseek/deepseek-v4-flash` through OpenRouter. All
other spans (input_guardrail, state_update, route_decision, product_search,
filter_and_rank, response_generation, output_validation, final_state) recorded
inputs, outputs, and metadata without any credential leakage.

Secret redaction: grep for `sk-lf-*`, `sk-or-*`, and other known secret
values found zero matches in observation payloads. Only the public key
(`pk-lf-*`) appears in SDK scope metadata as designed.

## Completion (archived)

**Status:** DoD satisfied. Tracker `docs/team/now/THANH-NOW.md` was overwritten
with a new mission on 2026-07-19; this section preserves the final state.

- **Full backend suite green** (2026-07-19, `AGENT_DATA_BACKEND=excel`,
  `OPENAI_API_KEY=""`): observability/graph/models 79 passed; agent + contract
  163 passed; other unit + eval 269 passed; integration 8 passed. Exclusions:
  `integration/api/test_catalog_endpoints.py` (live Postgres — see below) and
  the pre-existing env-sensitive `test_refinements.py::test_resolve_candidates_from_minimal_env`
  (also fails on `main`; unrelated to observability).
- **Re-instrumented after `main` refactor** (commit `3068a66`): main added new
  intents (smalltalk, product_qa, catalog_overview, price_range_query,
  promotion_inquiry, question_clarification) and restructured flows. The
  observability layer was re-applied on top of main's refactored
  `backend/app/agent/graph.py` (conflict resolved by taking main's whole file
  and re-adding the 4 helpers + per-node spans). Span names are frozen; the
  span-order contract in `backend/tests/unit/agent/test_observation_paths.py`
  still passes.
- **Observability tracking doc created:**
  `docs/team/now/OBSERVIBILITY-NOW.md` — single source of truth for the
  Langfuse instrumentation map, adapter invariants, test contract, and the
  re-instrumentation procedure for future `main` syncs. Owned by
  dinh-nhat-thanh (delegated in `docs/team/now/README.md`).
- **Live-Postgres integration test resolved** (2026-07-19): stood up Postgres
  via the dev override and ran the previously-deferred
  `backend/tests/integration/api/test_catalog_endpoints.py` — 13/13 passed.
  Full reproduction: `docs/reports/local-postgres-setup-report.md`.
- **Landed on `main`** (2026-07-19): `observation` fast-forwarded to contain
  `main`, then merged back. Remote commit `09ca0d5`.
