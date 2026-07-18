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

### Recorded evidence (2026-07-19)

Focused suite (`backend/tests/unit/observability backend/tests/unit/graph
backend/tests/unit/models backend/tests/contract/test_m1_contracts.py`):
**70 passed**.

Full backend suite (`AGENT_DATA_BACKEND=excel`): **354 passed, 1 skipped** in
33.6s. The `psycopg[binary]` + `psycopg-pool` drivers are now installed, so the
ingestion unit tests run and pass. Only `integration/api/test_catalog_endpoints.py`
is excluded: its fixtures open a live connection to a running Postgres server,
which the local environment does not host (the driver alone cannot substitute).
The 1 skip is the pre-existing empty-parameter-set golden eval, unrelated to
this story.

Note: installing `psycopg` makes `agent/catalog/pg_adapter.postgres_available()`
attempt a real TCP connect on the Excel-vs-Postgres probe, which blocks until
timeout when no server is running. Setting `AGENT_DATA_BACKEND=excel` (the
adapter's documented override) forces the Excel fallback and keeps the suite
hermetic; this is an environment concern owned by the data-platform story, not
an observability regression.

Dependencies unchanged — no `pyproject.toml`/lock edits — so lock validation is
a no-op for this story. `git diff --check` reports no whitespace errors.

Implemented priority observations under an active `advisor_turn` (sanitized;
no credentials, no auth headers, no environment secrets in any payload):

```text
advisor_turn
├── input_guardrail        # raw message in, guardrail flags/blocked out
├── intent_classifier      # raw message in, resolved intent out
│   ├── intent_model_call  # generation, one per candidate/retry attempt,
│   │                      #   raw model I/O + role/provider/model metadata
│   └── deterministic_fallback  # span, only when provider/schema call fails
└── state_merge            # before/after workflow state
```

Node outputs and existing M1 contracts are unchanged: every node defaults to
the US-207 no-op adapter, and the focused suite asserts identical outputs with
and without an observer.

### Live Langfuse smoke trace (2026-07-19)

**Trace ID:** `9a7e6a4216344b009ac432aac251651e`
**Langfuse URL:** `https://jp.cloud.langfuse.com/project/cmrqtlknr008vad0dwhwviuv6/traces/9a7e6a4216344b009ac432aac251651e`
**Observer:** `LangfuseAgentObserver` (live, not no-op)
**Environment:** `AGENT_DATA_BACKEND=excel`, no `OPENAI_API_KEY` (OpenRouter
route used for the understanding model call via the existing LLM client)
**Input message:** `tư vấn máy lạnh cho phòng 20m2`
**Resulting intent:** `new_search` (confidence 0.95, category_code 36)

Verified observation tree (all spans nested under the root `agent_turn`):

```text
agent_turn
├── input_guardrail          # SPAN — message in, blocked=false, flags out
├── understanding            # SPAN — message + state_summary in
│   └── understanding_model_call  # GENERATION — deepseek/deepseek-v4-flash,
│                                  #   full system/user prompt + structured output
├── state_update             # SPAN — before/after state, memory_delta
├── route_decision           # SPAN — intent → product_flow
├── product_search           # SPAN — category/budget/brand in, product_ids out
├── filter_and_rank          # SPAN — domain filters + role-based suggestions
├── response_generation      # SPAN — final text, intent, flags, presented_ids
├── output_validation        # SPAN — text + allowed_products in, ok/violations out
└── final_state              # SPAN — session state snapshot
```

The M1 standalone nodes (`intent_classifier`, `intent_model_call`,
`deterministic_fallback`) and `state_merge` from `backend/app/graph/nodes/` are
wired identically to the same observer and assert output-equivalence in the
focused unit suite (70 tests). They are exercised on the M1 graph path, not the
E02 agent path; both share the same `LangfuseAgentObserver` adapter.

**Secret redaction check:** grep of the full trace JSON for known secret
values (`sk-lf-*`, `sk-or-*`, `MISTRAL_API_KEY`, `AI_LOG_API_KEY`,
`JINA_API_KEY`) found **zero matches in any observation payload**. The only
hit was the `pk-lf-*` public key in the SDK scope metadata (expected and safe).
Both redaction layers (`_is_secret_key` key-based + `_secret_values` env-value
substring, ≥ 8 chars) are confirmed active.
