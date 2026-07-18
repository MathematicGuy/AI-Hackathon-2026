# Handoff — M1.3 complete, US-105 is next (2026-07-18)

Paused by Cường after the M1.3 chain landed. This file tells the next agent
exactly where to resume. Read `AGENTS.md` first — every gate there (session
log, read gate, Harness bootstrap/intake, bounded context) still applies.

## State snapshot (main @ 655841e, pushed, divergence 0/0)

Implemented and proven on `main` (full backend suite: **108 passed**):

| Story | What it delivered | Proof |
| --- | --- | --- |
| US-100 / US-121 / US-106 | Frozen contracts, executable reconciliation, catalog pagination | pre-existing (Thành's lane) |
| US-122 | Documentation governance (docs/ authority registry, validators) | governance validator |
| US-104 | `WorkflowState` + pure `merge_state` (correction precedence, invalidation) | trace #4, 3/3 |
| US-123 | Vietnamese business-KPI / viability / pilot-pathway baseline | trace #5 |
| US-102 | Layered input guardrail (word→regex→NeMo→scope, fail-closed, no-overfire) | trace #7, 3/3 |
| US-103 | Intent/need extraction (injected `gpt-5.4-nano` adapter + deterministic fallback) | trace #8, 3/3 |

Governance: Cường owns BOTH tracker aliases (`USER1`, `USER2`) — mapped in
`docs/team/now/README.md`; the governance validator allows multi-alias
ownership. Merge policy approved by Cường: self-merge to `main` after tests +
independent review. Commit messages: descriptive, **no** Co-Authored-By.

## Next story: US-105 — clarification, routing, persistence (M1.4, USER2 lane)

**Dependencies are met** (US-103 and US-104 are both on `main`). Before coding:

1. Complete the AGENTS.md preflight (own session log; identity = ask, never infer).
2. Bootstrap Harness; record intake; create + register the story packet (none
   exists yet). Persistence/checkpointer touches the data-model flag — expect
   high-risk lane per `docs/FEATURE_INTAKE.md`.
3. File boundary (from `docs/team/now/USER2-NOW.md`, verbatim):
   - `backend/app/domain/air_conditioner/clarification.py`
   - `backend/app/graph/nodes/router.py`
   - `backend/app/graph/nodes/clarify.py`
   - `backend/app/memory/__init__.py`
   - `backend/app/memory/checkpointer.py`
   - `backend/tests/unit/domain/air_conditioner/test_clarification.py`
   - `backend/tests/unit/graph/nodes/test_router.py`
   - `backend/tests/integration/memory/test_checkpointer.py`
4. Frozen constraints that bind US-105 (contract/PRD/tracker): one question per
   response, ≤3 per cycle, `force_exactly_three_questions: false`; router maps
   the 8 intents exactly per architecture §3; `session_id` → LangGraph
   `thread_id` (AsyncSqliteSaver); cross-session Store memory stays a
   feature-flagged no-op in M1; clarification asks only when missing info
   materially changes eligibility/capacity/hard constraints/role winners/
   primary-priority interpretation.
5. TDD: RED before GREEN (`uv run --python 3.12 --extra test pytest …`, exact
   commands in USER2-NOW); independent review; Harness proof + detailed-tier
   trace (numeric duration/tokens as labeled estimates); update only
   `docs/team/now/USER2-NOW.md`; then run `harness audit` **and** `harness
   propose` and explain both in the walkthrough.

**Cường's product principle (applies to clarification policy too):** never
overfire on legitimate requests; minimize engaging unrelated ones. For US-105:
ask only material questions, never re-ask answered ones, and keep unsupported
chit-chat in the scope-safe path.

## Environment notes

- Tests: `uv` + Python 3.12 (`--extra test`); `rtk` does not exist.
- The governance validator needs `rg` on PATH — a ripgrep binary exists at
  `…\cursor\resources\app\node_modules\@vscode\ripgrep\bin` (prepend for the
  session).
- Harness DB is local/ignored; this workspace's DB holds US-025/121/122/104/123/
  102/103. US-100/US-106 rows live only in Thành's workspace DB.

## Outstanding (not US-105)

- Scope-keyword duplication between `backend/app/guardrails/input_rules.py`
  and `backend/app/graph/nodes/intent.py` — small consolidation story; crosses
  US-102/US-103 file boundaries, so it needs its own registered story.
- Duy's mock SQLite catalog is still pending; defining the DB/data contract
  with him early avoids rework (crawler branch lacked an air-conditioner
  category as of 17/7).
- US-118 story-ID collision: `origin/frontend` reuses US-118 (SQLite catalog
  API) while `main` reserves US-118 (release-gate report) — integration
  controller (Thành) must resolve before frontend merge.
- CI `backend-tests` workflow is new — verify its first run on GitHub Actions.
- UI lives on `origin/frontend`; do not build UI here, it merges later.
