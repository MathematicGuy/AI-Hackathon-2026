# US-207 Langfuse Observation Implementation Handoff

## Purpose

Continue US-207 implementation immediately in the existing isolated worktree.
Do not reopen approved design decisions. Use the story packet as authority:

- `docs/stories/epics/E02-multi-category-agent/US-207-langfuse-agent-observability/`
- Execution plan: `docs/stories/epics/E02-multi-category-agent/US-207-langfuse-agent-observability/execplan.md`
- Coordination: `docs/team/now/THANH-NOW.md`

## Exact Workspace State

- Worktree: `E:\VIN-INTERNSHIP\AI-Hackathon-2026\.worktrees\observation`
- Branch: `observation`
- HEAD/base: `fd583ef` (`main` and `observation` both pointed here when checked)
- Git state before this handoff: only
  `backend/tests/unit/observability/test_langfuse.py` was untracked.
- No US-207 production module exists yet. No implementation commit exists.
- Root Harness matrix reports US-207 `planned`, `runnable=yes`; intake/partial
  trace is `#25`.

## Work Completed

- Approved spec and four-task exec plan already exist at paths above.
- Observation worktree created from current `main`.
- Task 1 RED test created:
  `backend/tests/unit/observability/test_langfuse.py`.
- RED verified with repository-safe pytest invocation. Decisive failure:
  `ModuleNotFoundError: No module named 'backend.app.observability'`.
- No production code written, so next action remains Task 1 GREEN.

Use this exact focused-test form on this machine:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
rtk proxy uv run --extra test python -m pytest -p pytest_asyncio.plugin -p no:cacheprovider backend/tests/unit/observability/test_langfuse.py -q
```

Why: plain `uv run pytest` failed to import top-level `backend`; manually
loading `pytest_asyncio` without disabling autoload registered it twice.

## Approved Decisions

- Explicit observation-boundary helper around agent flow and provider calls.
- One root `agent_turn` per request; important diagnostic children only.
- Capture full raw user/model prompts and outputs.
- Recursively redact secret-keyed values such as `api_key` and
  `authorization`; never record credentials or environment secret values.
- Fail open: Langfuse start/update/end/flush failures never change agent
  response, status, routing, or fallback behavior.
- Preserve SDK constraint `langfuse>=3,<4`; current lock is `3.15.0`.
- Use `ContextVar` parentage so concurrent async turns do not share parents.
- No sampling for E02 turns.

Priority tree is already defined in the plan: root, guardrail, understanding,
provider attempts/fallback, state update, route, retrieval/search,
filter/rank, response generation, output validation, and final state.

## Start Here

1. Fetch current Langfuse Python v3 instrumentation docs; do not code SDK calls
   from memory.
2. Strengthen Task 1 RED coverage before production code where needed:
   recursive/case-insensitive secret keys, update/end failure containment,
   disabled/missing-key default factory behavior, and async `ContextVar`
   isolation are required by the plan but not fully covered by current test.
3. Create only:
   - `backend/app/observability/__init__.py`
   - `backend/app/observability/langfuse.py`
4. Implement minimal Task 1 GREEN: protocols/handles, Langfuse adapter, no-op
   adapter, factories, safe serialization/redaction, nesting, fail-open
   lifecycle, flush.
5. Run focused GREEN, inspect diff, then follow Tasks 2-4 in exec plan using a
   fresh RED-GREEN cycle for each task.
6. Update existing session log at durable milestones:
   `ai-logs/dinh-nhat-thanh/sessions/2026-07-18T10-26-09Z_codex_langfuse-observation.md`.

## Do

- Work only inside `.worktrees/observation` on `observation`.
- Prefix shell commands with `rtk`; use `apply_patch` for file edits.
- Prefer codebase-memory MCP graph tools for symbol/call-path discovery.
- Keep raw diagnostic payloads, but scrub secret dictionary keys before any SDK
  call, including nested dictionaries/lists and model-attempt error metadata.
- Preserve existing graph order, fallback candidates, response bodies, and API
  status codes.
- Ask technical questions with brief context. If offering choices, explain
  pros, cons, and why each option matters; user is learning AI engineering.
- Use concise chat style only; keep code, docs, commits, and logs normal.

## Do Not

- Do not re-brainstorm or change approved scope without a real conflict.
- Do not trace every helper or add speculative observation abstractions.
- Do not implement US-116 in this branch phase. Its M1 files overlap current
  USER1/USER2 ownership and remain blocked pending integration control.
- Do not touch `resources/`.
- Do not add SDK v4, sampling, retention policy, prompt migration, scoring, or
  behavior changes.
- Do not expose `.env` values, API keys, authorization headers, or raw secrets
  in tests, traces, logs, handoffs, commands, or responses.
- Do not claim completion until focused tests, full backend tests,
  `uv lock --check`, and `git diff --check` pass freshly.

## Environment Finding

Harness executable and `harness.db` exist only in repository root, not this
worktree. Running worktree bootstrap currently fails with:
`Harness CLI is missing; install Harness again from its pinned release`.
Running root CLI from worktree then fails because worktree `harness.db` is
absent. Root read-only matrix query works and shows US-207/US-116 planned and
runnable. Do not silently initialize or duplicate Harness state; use root
Harness context for evidence or resolve setup with integration controller.

## Suggested Skills

- `superpowers:using-superpowers` — enforce applicable workflow skills first.
- `superpowers:executing-plans` — execute existing plan without redesign.
- `superpowers:test-driven-development` — preserve RED-GREEN-refactor per task.
- `langfuse` — fetch current SDK docs before instrumentation.
- `context7-mcp` — SDK/API documentation fallback when needed.
- `superpowers:verification-before-completion` — fresh proof before claims.
- `superpowers:finishing-a-development-branch` — only after all four tasks and
  final verification complete.
- `caveman` — concise direct replies only, never repository artifacts.

## Final Verification Contract

Use commands from Task 4, but keep plugin autoload disabled if this environment
repeats the observed plugin collision. Verify traced and no-op behavior remain
equal, secret material is absent, lockfile remains unchanged, then record
US-207 validation/Harness proof. Do not merge or begin US-116 without user and
integration-controller direction.
