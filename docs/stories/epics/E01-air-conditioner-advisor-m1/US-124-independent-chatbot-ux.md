# US-124 Independent Chatbot Browsing Experience

## Status

implemented

## Lane

normal

## Product Contract

The existing chatbot in `frontend/` is easy to notice, read, and operate without
preventing customers from browsing the storefront. On desktop, chat and page
browsing remain independent: the compact panel does not dim the page, lock page
scroll, or trap keyboard focus. On mobile, the panel remains modal to prevent
accidental interaction with obscured page content. This UI-only slice does not
add a live advisor API dependency or change supplied recommendation truth.

## Relevant Product Docs

- `docs/product/air-conditioner-advisor-m1-contract.md`
- `docs/product/requirements/air-conditioner-advisor-m1-prd.md` (§§4.14–4.18,
  16)
- `docs/product/architecture/air-conditioner-advisor-m1.md` (§§5.1, 7.5,
  8.2–8.4)

## Acceptance Criteria

- At viewport widths of 768px and above, the chatbot panel is at most 520px
  wide; the page stays visible, scrollable, clickable, and keyboard reachable.
- Desktop chat is non-modal: it has no page backdrop, body scroll lock, or focus
  trap. Mobile chat retains a backdrop, body scroll lock, safe-area spacing, and
  a contained focus loop.
- Opening desktop chat focuses the composer; opening mobile chat does not summon
  the software keyboard. Closing with `Escape` or the close control restores
  focus to one launcher control.
- The welcome text is useful across storefront routes and does not imply that a
  live human agent or an air-conditioner-only flow is active.
- Onboarding is removed after the first message so the active conversation gets
  priority.
- Header, messages, timestamps, composer, and disclaimer have readable contrast;
  unavailable mock controls are not presented as working actions.
- Comparison results expose prices and trade-offs before the product actions,
  retain visible product association on each action, and provide an explicit,
  keyboard-focusable horizontal-scroll affordance.
- Existing storefront routes, supplied product values, badges, rating data, and
  reply-selection logic remain unchanged.

## Design Notes

- Commands: `npm --prefix frontend run lint`, `typecheck`, and `build`.
- Queries: none; live advisor integration remains outside this story.
- API: preserve the current mock-first component boundary.
- Tables: none.
- Domain rules: render supplied values; do not recalculate eligibility, ranking,
  prices, badges, or evidence.
- UI surfaces: launcher, responsive panel, header, messages, prompt controls,
  composer, and comparison result.

## File Boundary

- `frontend/src/components/ChatbotAssistant.tsx`
- `frontend/src/components/chat/ChatComparisonResult.tsx`
- `frontend/src/app/globals.css`

## Implementation Plan

1. Capture desktop and narrow-viewport baselines and record usability issues.
2. Apply bounded visual, interaction, focus, responsive, and comparison-order
   improvements without changing product data or response logic.
3. Verify desktop independent browsing, mobile modal behavior, keyboard flow,
   static checks, and the production build.

## Validation

When updating durable proof status, use numeric booleans:
`scripts/bin/harness-cli story update --id US-124 --unit 0 --integration 0 --e2e 1 --platform 1`.

| Layer | Expected proof |
| --- | --- |
| Unit | No unit harness exists for this bounded visual change. |
| Integration | No backend integration; mock-first behavior only. |
| E2E | Chromium interaction checks for desktop independent browsing and mobile modal behavior. |
| Platform | Desktop plus narrow 320/400 CSS-pixel viewport visual checks. |
| Release | `npm --prefix frontend run lint && npm --prefix frontend run typecheck && npm --prefix frontend run build`. |

## Harness Delta

Normal-lane change request: existing user-visible behavior plus initially weak
visual proof, with no auth, data, provider, or API-contract change. This story
is independent of the original US-115 mock-first/API-swappable deliverable.

## Evidence

- `harness-cli story complete US-124` passed on 2026-07-18 and passed again
  after the header-clipping regression fix. Its fresh
  `npm --prefix frontend run check` completed ESLint, `tsc --noEmit`, and a
  production Next.js build of all 66 routes.
- Production Chromium at 1442x788 rendered a 520px desktop panel with
  `aria-modal="false"`, no backdrop or body scroll lock, and keyboard focus
  able to move into the storefront. Page scrolling remained available while
  chat stayed open.
- Desktop `Escape` from storefront focus left chat open and preserved that
  focus. `Escape` from inside chat closed it and restored focus to the single
  launcher.
- Production Chromium at 502px, 400px, and 320px rendered a modal panel with
  8px side insets, no document-level horizontal overflow, a backdrop, body
  scroll lock, and initial focus on the close control instead of the composer.
- Comparison interaction exposed the horizontal-scroll hint and the distinct
  `Xem Casper`, `Xem Midea`, and `Xem Nagakawa` actions after the comparison
  details. Onboarding collapsed after the first message.
- A reported comparison screenshot showed `scrollIntoView` had scrolled the
  outer clipped panel and moved its header out of view. Auto-scroll now targets
  only the conversation container.
- Production Chromium after the fix measured outer panel `scrollTop=0` and
  conversation `scrollTop=180` on desktop and a 400px mobile viewport. The
  header stayed aligned with the panel top, the footer remained visible, and
  mobile modal/body-lock behavior was preserved.
- Independent review found no remaining US-115/US-124 ownership blocker after
  the split. Its final desktop `Escape` isolation finding was fixed and
  rechecked in the production bundle.
- The build emitted the existing non-blocking Next.js warning about multiple
  lockfiles and inferred Turbopack workspace root; compilation still passed.
