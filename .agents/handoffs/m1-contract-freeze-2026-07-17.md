# M1.0 contract freeze handoff

## Current state

- Branch: `agent/m1-implementation`.
- Completed story: `US-100 — M1 Contract Freeze`.
- Harness trace: `#8` (detailed, meets high-risk requirement).
- Contract proof: 7 tests pass under `backend/tests/contract`.
- Harness audit: 0 orphaned stories, entropy `0/100`.

## Frozen decisions

- Use `deepseek/deepseek-v4-flash` through OpenRouter for M1 grounded
  explanations. Never use GPT-5.4 Mini for this role.
- Keep GPT-5.4 Nano for intent classification and need extraction.
- Deterministic code owns normalization, filtering, ranking, role selection,
  and display deduplication.
- Use only `data/aircon-m1-test-data/` for M1 fixture proof. Its 14 catalog
  products and 26 evaluation cases are synthetic.
- `AIRCON-M1-001` winners are AC-M1-002, AC-M1-003, and AC-M1-006 for Best
  Overall, Best Value, and Cheapest Qualified.

## Implemented artifacts

- Product contract: `docs/product/air-conditioner-advisor-m1-contract.md`.
- Decision: `docs/decisions/0009-m1-explanation-model-routing.md`.
- Story packet:
  `docs/stories/epics/E01-air-conditioner-advisor-m1/US-100-m1-contract-freeze/`.
- Schemas: `backend/app/contracts/schemas.py`.
- Graph constants: `backend/app/graph/node_names.py`.
- Mock and fixture proof: `backend/tests/contract/`.

## Next action

Select exactly one M1.1–M1.4 story, create its packet and durable record, and
implement its smallest vertical slice with TDD. Do not create all packets
upfront. M1.1 catalog normalization is the recommended next slice because it
turns the committed catalog into the typed product contract needed by filtering
and ranking.

## Constraints

- Preserve unrelated dirty work listed by `git status --short`.
- Ignore `resources/` unless the user explicitly requests it.
- Do not treat the test-only ranking fixture as approved production ranking.
- The repository-wide AI logging validator currently fails on pre-existing
  missing `GEMINI.md` and AGENTS logging-block placement; do not conflate that
  with the passing M1.0 proof.
