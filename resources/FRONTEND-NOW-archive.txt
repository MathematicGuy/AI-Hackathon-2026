# FRONTEND Current Mission

## Outcome

Replace the hard-coded chatbot comparison in `frontend/` with an additive,
server-owned E02 presentation payload that matches the storefront renderer.

## Owner

- Tracker alias: `FRONTEND`
- Member identity: `nguyen-phuong-hoai-ngoc`
- Story: `US-125` (`in_progress` after ownership and verification registration)
- Branch: `deploy` (assigned by Ngọc's explicit human direction on 2026-07-19 for US-125 planning)
- Worktree: `E:\VAI\AI-Hackathon-2026`

## Ownership Boundary

This lane owns only:

- `frontend/src/components/ChatbotAssistant.tsx`
- `frontend/src/components/chat/ChatComparisonResult.tsx`
- `frontend/src/app/globals.css`
- `frontend/src/lib/agent-api.ts`
- `frontend/src/types/agent.ts`
- targeted US-125 tests and test setup under `frontend/src/`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/vitest.config.ts`
- `backend/app/agent/api.py`
- `backend/app/agent/contracts.py`
- `backend/app/agent/graph.py`
- `backend/app/agent/respond.py`
- `backend/app/agent/presentation.py`
- `backend/tests/contract/test_agent_api_contract.py`
- `backend/tests/unit/agent/test_presentation.py`
- `backend/tests/integration/api/test_agent_endpoint.py` when cross-stack proof requires it
- `scripts/verify-us125.ps1`
- `scripts/verify-us125-ui.py`
- `docs/decisions/0017-e02-structured-chatbot-presentation.md`
- `docs/stories/epics/E02-multi-category-agent/US-125-structured-storefront-chatbot-presentation/`
- `docs/team/now/FRONTEND-NOW.md`

Ngọc's explicit human direction on 2026-07-19 authorizes this tracker and its
identity-map row to use branch `deploy` for US-125. The same direction assigns
only the E02 presentation-contract backend files named above because the prior
E02 contract had not been finalized. Cường retains all other E02 scope. Do not
edit another member's tracker, ranking logic, catalog data, or unnamed backend
files.

## Dependencies

- ADR-0017 accepts an additive `presentation` payload on the shipped E02
  `/api/v1/agent/respond` endpoint while retaining `text` as fallback.
- Ngọc explicitly owns the named E02 presentation-contract slice on `deploy`;
  backend contract/test work precedes frontend consumption.
- The backend contract must ship before `frontend/` depends on `presentation`.
- `frontend-mvp/` and the M1 `/api/v1/advisor/respond` path are out of scope.
- The frontend must render supplied fields without recalculating eligibility,
  ranking, role badges, prices, or evidence.

## Execution Board

| Order | Work | Status |
| ---: | --- | --- |
| 1 | Register intake, ADR-0017, and US-125 plan | Complete |
| 2 | Assign E02 presentation files and register verification | Complete |
| 3 | Add and prove the structured E02 presentation contract | Complete |
| 4 | Replace frontend query heuristics/static comparison with typed rendering | In progress |
| 5 | Run contract, cross-stack E2E, build, and desktop/mobile proof | Pending |

## Verification

```powershell
uv run --no-project --isolated --python 3.12 --with-editable ".[test]" --no-env-file python -m pytest backend/tests/contract/test_agent_api_contract.py backend/tests/integration/api/test_agent_endpoint.py -q
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

The Harness verification command is `scripts/verify-us125.ps1`. Visual proof
must cover desktop and mobile layouts, keyboard focus, text fallback,
recommendation cards, and comparison-result scanning.

## Constraints

- Preserve the storefront outside the chatbot.
- Keep Vietnamese customer-facing copy concise and legible.
- Missing product data remains visibly unknown; never infer it.
- A product renders once even when it carries multiple role badges.
- Never show comparison UI unless the server supplies a comparison presentation.
- Never use `frontend-mvp/` as an implementation or runtime dependency.
- Ignore `resources/`.
