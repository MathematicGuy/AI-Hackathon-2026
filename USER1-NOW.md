# USER1 Current Mission

## Outcome

Deliver the M1.3 input guardrail and Vietnamese intent/need extraction chain so validated structured needs can feed the M1.4 and M1.5 workflows.

## Ownership boundary

USER1 owns only:

1. US-102 — layered input guardrail.
2. US-103 — Vietnamese intent and need extraction, after US-102 is reviewed and merged.

No later story is implied. Thành remains the integration controller. Update only `USER1-NOW.md`; do not edit `THANH-NOW.md`, `USER2-NOW.md`, or create another progress ledger.

## Start point and isolation

- Required base: local `main` containing at least merge `9dc9363`.
- Branch: `agent/user1-m1-3-guardrails-intent`.
- Work in an isolated worktree or clone. Never implement concurrently in Thành's or USER2's working tree.
- Before work, resolve your real team identity through `ai-logs/README.md`, create the correct session log, bootstrap Harness, and confirm the active matrix in your worktree.

## Execution board

| Order | Story | Depends on | Status | Detail source |
| ---: | --- | --- | --- | --- |
| 1 | US-102 layered input guardrail | US-121 complete | Ready to activate | Task 6 in `docs/superpowers/plans/2026-07-17-m1-1-through-m1-8.md` |
| 2 | US-103 Vietnamese intent/need extraction | Reviewed US-102 merged to main | Blocked until US-102 merge | Task 7 in the same plan |

Activate only the current story in this worktree. For each story: record the base commit, run RED before production edits, implement the minimum GREEN change, run independent verification, obtain a separate review, close Critical/Important findings, complete Harness proof/trace, update this ledger, and submit the reviewed commit hash to Thành.

## File boundary

US-102 owns only:

- `backend/app/guardrails/__init__.py`
- `backend/app/guardrails/input_rules.py`
- `backend/app/guardrails/nemo/__init__.py`
- `backend/app/guardrails/nemo/input.py`
- `backend/app/graph/nodes/input_guard.py`
- `backend/tests/unit/guardrails/test_input_rules.py`
- `backend/tests/unit/graph/nodes/test_input_guard.py`

US-103 owns only:

- `backend/app/models/__init__.py`
- `backend/app/models/openai_intent.py`
- `backend/app/graph/nodes/intent.py`
- `backend/tests/unit/models/test_openai_intent.py`
- `backend/tests/unit/graph/nodes/test_intent.py`

Do not edit decision-engine files under `backend/app/domain/air_conditioner/`, workflow state/memory files, frozen contracts, another user's NOW file, or shared package files not named above. Stop and ask Thành if a shared contract change appears necessary.

## Verification

US-102 RED and GREEN:

```powershell
rtk pytest backend/tests/unit/guardrails backend/tests/unit/graph/nodes/test_input_guard.py -q
```

US-103 RED:

```powershell
rtk pytest backend/tests/unit/models/test_openai_intent.py backend/tests/unit/graph/nodes/test_intent.py -q
```

US-103 GREEN and contract check:

```powershell
rtk pytest backend/tests/unit/models/test_openai_intent.py backend/tests/unit/graph/nodes/test_intent.py backend/tests/contract -q
```

## Merge handoff

1. Submit reviewed US-102 with its proof and trace to Thành.
2. Wait for US-102 to reach main, then refresh this branch from main.
3. Implement and submit reviewed US-103 with its proof and trace.
4. Notify USER2 and Thành that US-103 is on main; this unlocks USER2's US-105 only after US-104 is also merged.

## Frozen constraints

- Input guard order is word count → regex/payload → NeMo → scope → intent classifier.
- Input blocks at 150 words or more; 149 words remains allowed.
- GPT-5.4 Nano owns intent classification and structured need extraction.
- Extraction preserves nulls and never invents numeric values.
- Deterministic code owns validation and fallback behavior.
- Synthetic fixtures under `data/aircon-m1-test-data/` must never be described as live Điện Máy XANH data.
- Request `gpt-5.6-luna-high` for context investigation and `gpt-5.6-terra-high` for implementation; do not claim enforcement if the runtime cannot select a model.
- Ignore `resources/`.
