# Handoff — US-207 + US-116 Langfuse agent observability: live-trace smoke before close

**Branch / worktree:** `observation` @ `E:\VIN-INTERNSHIP\AI-Hackathon-2026\.worktrees\observation`
**Owner:** Đinh Nhật Thành (sole owner of the M1 node files — overlap resolved, see `fc4e891`)
**Date:** 2026-07-19

## Scope of the remaining task (only this)

Capture **one smoke trace against a REAL Langfuse project** and attach the evidence, then close US-207 and US-116. All code and in-memory/fake-observer test evidence is already done and committed. Do **not** re-implement or re-verify the adapter — the story validation plan explicitly scoped complete-tree/live evidence as out of story; this is the final manual confirmation the user asked for before closing.

## Definition of Done for this session

1. A real Langfuse project receives a trace from one agent turn showing the priority tree:
   `advisor_turn → {input_guardrail, intent_classifier → (intent_model_call generation, deterministic_fallback span), state_merge}`.
2. Confirm **no secrets** in the trace payloads (API keys, auth headers, env secret values). Redaction is enforced by `_is_secret_key` + `_secret_values` in `backend/app/observability/langfuse.py`.
3. Record the evidence (trace URL/screenshot, sanitized) in
   `docs/stories/epics/E01-air-conditioner-advisor-m1/US-116-langfuse-agent-observability/validation.md`
   under the existing "Recorded evidence" section, and mark both stories done in `docs/team/now/THANH-NOW.md`.

## How enablement works (verified this session — do not guess)

`backend/app/observability/langfuse.py:359 default_agent_observer()`:
- Enabled when `LANGFUSE_ENABLED` (default `true`) AND `LANGFUSE_PUBLIC_KEY` AND `LANGFUSE_SECRET_KEY` are set; optional `LANGFUSE_BASE_URL` → SDK `host`. Missing keys or any construction error → silent `NoopAgentObserver` (fail-open). SDK `langfuse` 4.14.0 is installed.
- Nodes accept an injected `observer` and default to `noop_agent_observer()`; the composition root that wires the live observer into a turn is `backend/app/agent/graph.py` (`AgentDependencies.from_default_paths()` → `default_agent_observer()`), consumed by `run_turn`.

### Suggested path to produce the trace
- Set the 3 Langfuse env vars to a real project (ask the user for keys — never hardcode; keep them out of commits and logs).
- **Set `AGENT_DATA_BACKEND=excel`** — otherwise `agent/catalog/pg_adapter.postgres_available()` opens a live TCP connect that blocks (see finding below).
- Run one turn via the demo CLI `backend/app/agent/demo.py` (or the agent API). `from_default_paths()` uses `with_llm=True`, so the main LLM path needs `OPENAI_API_KEY` (gpt-4o-mini, per AGENTS.md learnings). If no OpenAI key, the deterministic fallback still fires and still produces `intent_classifier` + `deterministic_fallback` spans — that alone is a valid smoke trace, just note the degraded path.
- After the turn, ensure `flush()` runs (the observer exposes it) so the trace exports before the process exits.

## What is already DONE (reference, do not redo)

- Implementation commits on `observation`: `d73df06` (Gap A: close model-failure observations safely), `c9ac711` (Gap B: guard short env secrets from over-redaction), `2420f6f` (trace M1 priority graph nodes), `9b4c5f6` (trace M1 intent model calls). Docs: `8d9f0ad`, `e65381f`, `b849d57`.
- Wired nodes: `backend/app/graph/nodes/{input_guard,intent,merge_state}.py`, `backend/app/models/openai_intent.py` (see diffs — each adds an optional `observer` kwarg + a span; outputs unchanged when observer is default no-op).
- Tests: `backend/tests/unit/graph/*`, `backend/tests/unit/models/test_openai_intent.py`, `backend/tests/unit/observability/test_langfuse.py`, shared fixtures in `backend/tests/unit/conftest.py` (`RecordingObserver`/`RecordingSpan`, `recording_observer`).
- Test evidence: focused suite **70 passed**; full backend suite **354 passed, 1 skipped** in ~34s (see validation.md). See commit diffs rather than re-reading all files.

## Session findings & patterns (save re-discovery time)

1. **psycopg install side effect (root cause of a full-suite hang):** once `psycopg[binary]`+`psycopg-pool` are installed, `agent/catalog/pg_adapter.postgres_available()` (line ~65) runs a real TCP connect to Postgres on the Excel-vs-Postgres probe; with no server running it blocks until timeout and hangs `integration/agent/test_smoke.py` and anything using `AgentDependencies.from_default_paths()`. **Fix/workaround: `AGENT_DATA_BACKEND=excel`** forces the Excel fallback (documented override). This is data-platform (US-206) territory — a skip-when-unreachable guard is a deferred follow-up, tracked in THANH-NOW.md "Deferred / Follow-ups" and in the deferred live-Postgres test.
2. **Deferred test:** `backend/tests/integration/api/test_catalog_endpoints.py` needs a *running* Postgres server (its fixtures connect directly). It is excluded from the full-suite pass via `--ignore`. Not observability-related; leave it deferred.
3. **Running pytest here:** from worktree root, `PYTHONPATH="$PWD" python -m pytest ... -p no:cacheprovider -q`. `PYTHONPATH` is REQUIRED (no conftest sets it → `ModuleNotFoundError: No module named 'backend'`). The harness caps each command at ~2 min — split the suite into sub-2-min chunks; an inner `timeout` larger than that never fires.
4. **rtk quirks:** `rtk` summarizes pytest output and can misleadingly say "No tests collected" — use `rtk proxy <cmd>` to see real output. For git: plain `git add` works; commit via `rtk proxy git commit -q -m "single message"` (multi-`-m` or `&&`-chained commands get blocked by the classifier).
5. **Redaction is two-layer:** key-based (`_is_secret_key`) + env-value substring (`_secret_values`, only values ≥ `_MIN_SECRET_VALUE_LENGTH`=8 to avoid corrupting text like "18m2"). Verify the live trace against both.

## Governance / gates (AGENTS.md)

This is manual verification + doc-recording (a change task touching validation.md). Follow the AGENTS.md gates: session-logging preflight (resolve identity — do not infer; ask the canonical identity question), repository read gate, then Harness bootstrap before editing repo artifacts. THANH-NOW.md is the only allowed product-progress ledger.

## Suggested skills for the next agent

- `superpowers:using-superpowers` — invoke first (session bootstrap rule).
- `superpowers:verification-before-completion` (or equivalent) — the task IS a verification/evidence step; do not claim the trace exists without seeing it in the Langfuse UI.
- `superpowers:test-driven-development` — only if a code change becomes necessary (e.g. adding the deferred skip-when-unreachable guard); not expected for the trace itself.
