# Exec Plan

## Goal

Deliver the M1.3 layered input guardrail with deterministic, short-circuiting
stages in the frozen order and fail-closed NeMo degradation, proven by unit
tests plus unchanged contract tests.

## Scope

In scope:

- `backend/app/guardrails/__init__.py`
- `backend/app/guardrails/input_rules.py`
- `backend/app/guardrails/nemo/__init__.py`
- `backend/app/guardrails/nemo/input.py`
- `backend/app/graph/nodes/input_guard.py`
- `backend/tests/unit/guardrails/test_input_rules.py`
- `backend/tests/unit/graph/nodes/test_input_guard.py`

Out of scope:

- US-103 (intent/need extraction) and output guardrails.
- Real NeMo/network integration; gateway→state wiring (US-101).
- Frozen contracts, decision engine, tools, UI, SQLite, other trackers.

## Risk Classification

Risk flags: audit/security (injection, scope, credential/hidden-prompt checks);
public contracts (frozen guardrail order); weak proof (new area).

Hard gates: audit/security → high-risk lane retained; direction is unambiguous
(frozen order and behavior), so no human confirmation is required beyond the
approved plan.

## Work Phases

1. Discovery — done (no implementation exists; `INPUT_GUARD_ORDER` frozen).
2. Design — `design.md`.
3. Validation planning — `validation.md`.
4. Implementation — RED tests first, then minimal GREEN on branch
   `agent/user1-m1-3-guardrails-intent`.
5. Verification — story verify command plus the full backend suite.
6. Harness update — proof, trace, completion; USER1 ledger.

## Stop Conditions

Pause for human confirmation if a frozen contract change appears necessary, a
new guardrail stage outside `INPUT_GUARD_ORDER` is required, validation must be
weakened, or ownership beyond the seven owned files is needed.
