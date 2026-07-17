# USER2 Current Mission

## Outcome

Deliver the M1.4 state and conversation-control chain so corrections, clarification, routing, and persistence are ready for the M1.5 vertical slice.

## Ownership boundary

USER2 owns only:

1. US-104 — internal workflow state and correction precedence.
2. US-105 — clarification, routing, and session persistence, only after both US-103 and US-104 are reviewed and merged.

No later story is implied. Thành remains the integration controller. After a
human maps USER2 to an identity, that owner updates only
`docs/team/now/USER2-NOW.md`; do not edit
`docs/team/now/THANH-NOW.md`, `docs/team/now/USER1-NOW.md`, or create another
progress ledger.

## Start point and isolation

- Required base: local `main` containing at least merge `9dc9363`.
- Branch: `agent/user2-m1-4-state-routing`.
- Work in an isolated worktree or clone. Never implement concurrently in Thành's or USER1's working tree.
- USER2 is currently unassigned in `docs/team/now/README.md`; implementation is
  blocked until a human maps the alias.
- Before work, resolve your real team identity through `ai-logs/README.md`, create the correct session log, bootstrap Harness, and confirm the active matrix in your worktree.

## Execution board

| Order | Story | Depends on | Status | Detail source |
| ---: | --- | --- | --- | --- |
| 1 | US-104 state merge and correction precedence | US-121 complete | Blocked until human mapping and a registered story packet | Legacy provenance only: Task 8 in `docs/superpowers/plans/2026-07-17-m1-1-through-m1-8.md` |
| 2 | US-105 clarification/routing/persistence | US-103 and US-104 merged to main | Blocked until mapping, packet, and both merges | Legacy provenance only: Task 9 in the same file |

Do not activate work directly from the legacy plan. After a human maps USER2,
create and read the registered story packet from accepted product authority,
then record the base commit, run RED before production edits, implement the
minimum GREEN change, run independent verification, obtain a separate review,
close Critical/Important findings, complete Harness proof/trace, update this
ledger, and submit the reviewed commit hash to Thành.

## File boundary

US-104 owns only:

- `backend/app/graph/state.py`
- `backend/app/graph/nodes/merge_state.py`
- `backend/tests/unit/graph/nodes/test_merge_state.py`

US-105 owns only:

- `backend/app/domain/air_conditioner/clarification.py`
- `backend/app/graph/nodes/router.py`
- `backend/app/graph/nodes/clarify.py`
- `backend/app/memory/__init__.py`
- `backend/app/memory/checkpointer.py`
- `backend/tests/unit/domain/air_conditioner/test_clarification.py`
- `backend/tests/unit/graph/nodes/test_router.py`
- `backend/tests/integration/memory/test_checkpointer.py`

Do not edit guardrail/intent files, decision-engine files other than the named clarification module, frozen contracts, another user's NOW file, or shared package files not named above. Stop and ask Thành if a shared contract change appears necessary.

## Verification

US-104 RED:

```powershell
rtk pytest backend/tests/unit/graph/nodes/test_merge_state.py -q
```

US-104 GREEN and contract check:

```powershell
rtk pytest backend/tests/unit/graph/nodes/test_merge_state.py backend/tests/contract -q
```

US-105 RED and GREEN:

```powershell
rtk pytest backend/tests/unit/domain/air_conditioner/test_clarification.py backend/tests/unit/graph/nodes/test_router.py backend/tests/integration/memory/test_checkpointer.py -q
```

## Merge handoff

1. Submit reviewed US-104 with its proof and trace to Thành.
2. Keep US-105 blocked until both US-103 and US-104 are on main.
3. After both merges, refresh this branch from main before writing the US-105 RED tests.
4. Submit reviewed US-105 with its proof and trace to Thành for serialized integration.

## Frozen constraints

- New explicit corrections override older explicit or inferred values; omitted values preserve current state.
- Explicit null is not deletion in M1; deletion requires a future explicit removal intent.
- Hard-constraint changes invalidate derived retrieval, eligibility, ranking, display, and output state without corrupting cursor or shown IDs during merge.
- Each clarification response contains one question; a clarification cycle contains at most three questions.
- Session persistence maps `session_id` to LangGraph `thread_id` and isolates different sessions.
- Optional cross-session Store memory remains a feature-flagged no-op in M1.
- Request `gpt-5.6-luna-high` for context investigation and `gpt-5.6-terra-high` for implementation; do not claim enforcement if the runtime cannot select a model.
- Ignore `resources/`.
