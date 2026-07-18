# Retrospective PR Report: Frontend MVP and Model Routing

## Status

This is a retrospective report, not a GitHub pull request. The referenced work
is already merged into local `main`; after synchronization,
`agent/m1-implementation` and `main` both resolve to `f40b7e3`.

## Scope

### Frontend MVP

| Task | Completed work | Evidence |
| --- | --- | --- |
| 1. Scaffold Next.js 15 + Tailwind + tooling | Created the `frontend-mvp` Next.js testing harness with TypeScript, Tailwind, npm scripts, environment template, and runbook. | `9a43f7d` |
| 2. Type contract + pure utilities | Added the advisor TypeScript contract plus session/request IDs, display and currency formatting, and product-card badge deduplication. | `733bc73` |
| 3. Mock products | Added normalized synthetic air-conditioner products that cover multi-role badges, availability states, and distinct alternatives. | `f71f580` |
| 4. Fixtures per answer type | Added canned `AdvisorResponse` fixtures for every supported `answer_type`, ready for deterministic mock scenarios. | `b5fb3f6` |

The completed frontend harness renders all eight response states and keeps one
data-source swap point through `NEXT_PUBLIC_ADVISOR_MODE`; later frontend
commits continue that implementation beyond Tasks 1-4.

### Environment-Owned Model Routing

The model-routing hardening work moved provider connections and role-specific
model choices to validated environment-backed settings. It rejects blank
credentials, resolves immutable routes for main, extraction, fallback, and
judge roles, separates routing from contracts, and documents the resulting
runtime configuration.

| Commit | Change |
| --- | --- |
| `ab6bc1f` | Defined the environment-owned routing design and execution plan. |
| `13d1e85` | Added the environment-driven settings boundary. |
| `9374fab` | Rejected whitespace-only provider credentials. |
| `0f29b18` | Resolved immutable routes for the required model roles. |
| `01f4f1b` | Separated runtime routing from the contract layer. |
| `fcda6ae` | Documented the environment-owned runtime routing configuration. |

The active workstream tracker records 34 settings tests, 9 routing tests, 8
contract tests, 51 focused backend tests, and 96 full-backend tests for this
completed scope. Those historical results are reported here; they were not
re-run for this documentation-only artifact.

## Integration Record

- `main` received the progress-reconciliation commit `f40b7e3`.
- `agent/m1-implementation` fast-forwarded from `f8989ab` to `f40b7e3`.
- The branch has no commits ahead of `main`, so creating a feature PR would
  misrepresent already-merged work.

## Validation

- Confirmed the frontend task names and commit history against the retained
  implementation plan and Git history.
- Confirmed the environment-owned routing commit sequence and recorded test
  evidence against the active workstream tracker.
- Confirmed `main...agent/m1-implementation` has no divergence after sync.
