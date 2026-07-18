# Exec Plan

## Goal

Deliver the M1.4 state-merge foundation: deterministic correction precedence,
assumption transitions, and hard-constraint invalidation, proven by unit tests
plus unchanged contract tests.

## Scope

In scope:

- `backend/app/graph/state.py`
- `backend/app/graph/nodes/merge_state.py`
- `backend/tests/unit/graph/nodes/test_merge_state.py`

Out of scope:

- US-105 files (clarification, router, checkpointer).
- Frozen contracts, guardrails, decision engine, tools, UI, SQLite, CI.
- Any other member's tracker file.

## Risk Classification

Risk flags:

- Existing behavior (frozen, contract-tested public state adjacent).
- Weak proof (no tests exist yet in the affected area).
- Public contract adjacency (public `AdvisorState` must not drift).

Hard gates:

- None triggered; high-risk lane retained per prior read-only assessment
  because the story introduces internal state schema and merge semantics under
  a frozen public contract.

## Work Phases

1. Discovery — completed in the 2026-07-17 read-only sessions (current main
   has no implementation; `model_fields_set` distinguishes omission from
   explicit null).
2. Design — recorded in `design.md`; bounded interpretations approved with the
   plan on 2026-07-18.
3. Validation planning — `validation.md`.
4. Implementation — RED tests first, then minimal GREEN on branch
   `agent/user2-m1-4-state-routing`.
5. Verification — story verify command plus the full backend suite.
6. Harness update — proof flags, trace, completion; USER2 ledger update.

## Stop Conditions

Pause for human confirmation if:

- A frozen contract change appears necessary.
- Merge semantics not covered by the accepted authority are required.
- Validation must be weakened to pass.
- File ownership outside the three owned paths is needed.
