# FRONTEND Current Mission

## Outcome

Make the existing chatbot in `frontend/` easier to scan and operate on desktop
and mobile while preserving the server-owned recommendation contract.

## Owner

- Tracker alias: `FRONTEND`
- Member identity: `nguyen-phuong-hoai-ngoc`
- Story: `US-115`
- Branch: `frontend`
- Worktree: `E:\VAI\AI-Hackathon-2026`

## Ownership Boundary

This lane owns only:

- `frontend/src/components/ChatbotAssistant.tsx`
- `frontend/src/components/chat/ChatComparisonResult.tsx`
- `frontend/src/app/globals.css`
- `docs/stories/epics/E01-air-conditioner-advisor-m1/US-115-approved-mock-first-frontend.md`
- `docs/team/now/FRONTEND-NOW.md`

The explicit human assignment also authorizes the one-time `FRONTEND` identity
row in `docs/team/now/README.md`. Do not edit another member's tracker, backend
files, product contracts, ranking logic, or catalog data.

## Dependencies

- Mock-first UI work depends on the completed US-121 mock contract and is ready.
- Real advisor API integration remains dependency-gated on M1.5-M1.7 and is out
  of scope for this UI review.
- The frontend must render supplied fields without recalculating eligibility,
  ranking, role badges, prices, or evidence.

## Execution Board

| Order | Work | Status |
| ---: | --- | --- |
| 1 | Register and align US-115 with current product authority | In progress |
| 2 | Capture a visual and interaction baseline | Pending |
| 3 | Apply bounded chatbot UX improvements | Pending |
| 4 | Run lint, typecheck, build, and desktop/mobile visual checks | Pending |

## Verification

```powershell
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

Visual proof must cover desktop and mobile layouts, keyboard focus, readable
message hierarchy, composer usability, and comparison-result scanning.

## Constraints

- Preserve the storefront outside the chatbot.
- Keep Vietnamese customer-facing copy concise and legible.
- Missing product data remains visibly unknown; never infer it.
- A product renders once even when it carries multiple role badges.
- Ignore `resources/`.
