# Handoff — frontend-mvp implementation (continue Tasks 9→11)

**Date:** 2026-07-18 · **Branch:** `agent/m1-implementation` · **Story:** US-115 (harness, `in_progress`)

## Scope for the next session

Finish executing `docs/superpowers/plans/2026-07-17-frontend-mvp.md`. Tasks 1–8 are
done and committed. Task 9 code is written but **not committed** — it is blocked on a
`next build` crash (see Blocker). Then do Task 10 (mandatory Playwright smoke) and
Task 11 (final verification), then `superpowers:finishing-a-development-branch`.

Do **not** re-derive the design — it is fixed in the spec and plan. Do not add features
beyond the 8 answer-type states. The plan step bodies contain exact file contents; follow
them verbatim.

## What is DONE (committed)

Commits `9a43f7d` → `e251c31` (8 tasks). Read `git log --oneline -8` for the list. This
covers: scaffold, `lib/types.ts` + id/format/dedupe utilities (+vitest, 5 tests green),
mock products, per-answer_type fixtures, scenario matcher + `lib/advisor-api.ts` swap point
(9 scenario tests green), shadcn primitives + advisor leaf components, product/summary/
premium/more components, and all 8 state components + `AnswerRenderer` (exhaustive switch,
typecheck green). 14/14 vitest pass. `tsc --noEmit` passes.

## What is WRITTEN but UNCOMMITTED (Task 9)

Working tree (see `git status`): `M frontend-mvp/app/page.tsx`, untracked
`frontend-mvp/components/chat/` (`MessageInput.tsx`, `MessageList.tsx`, `ChatPanel.tsx`),
and generated `frontend-mvp/next-env.d.ts`. Typecheck on this code **passes**. Commit it
with the Task 9 message once the build is unblocked. Also still uncommitted from intake:
`docs/stories/epics/E01-air-conditioner-advisor-m1/US-115-approved-mock-first-frontend.md`
and the restored `docs/superpowers/plans/2026-07-17-frontend-mvp.md` — commit both.

## BLOCKER — `next build` OOM (root cause: node 24 ↔ Next 15.1.0)

`npm run build`: compiles ✓ and type-checks ✓, then crashes during **"Collecting page
data"** with `FATAL ERROR: Committing semi space failed. Allocation failed - JavaScript
heap out of memory` at only ~104 MB used. Raising the heap
(`NODE_OPTIONS=--max-old-space-size=4096 --max-semi-space-size=128`) did **not** help — so
it is not genuine memory pressure. Runtime is **node v24.16.0**; Next 15.1.0 predates node
24. `next@15.1.0` also carries a flagged CVE (CVE-2025-66478) — already noted at scaffold time.

Recommended fixes, in order of preference:
1. **Bump Next.js to a node-24-compatible patched 15.x** (e.g. latest `15.x`) in
   `frontend-mvp/package.json`, `npm install`, retry build. This resolves both the OOM and
   the CVE. Verify `react`/`react-dom` 19 stay compatible. This is a deviation from the
   plan's pin — record it (append to the plan's changelog / a decision note) and mention it
   in the walkthrough.
2. If a version bump is undesirable, **use node 22 LTS** (nvm) for the build; the pinned
   toolchain was authored against node 22.
3. `next dev` does **not** run the page-data collection that crashes, so the **Playwright
   E2E (Task 10) should pass regardless** — `playwright.config.ts` boots `npm run dev`. You
   can proceed to Task 10 to unblock the mandatory smoke test even before fixing `build`,
   but Task 11's DoD requires `build` green, so fix it before finishing.

Confirm with the user before choosing option 1 vs 2 (dependency bump vs runtime change) —
either is a real change to the declared toolchain.

## Definition of Done

- `cd frontend-mvp && npm run typecheck && npm run test && npm run build && npm run test:e2e` all green.
- Playwright drives all 8 answer_types and asserts dedup (AC_DAIKIN renders once with 2 badges) — Task 10.
- Task 11 guard: grep confirms no component imports mock fixtures directly (only `lib/advisor-api.ts` does).
- All Task 9–11 files committed; `harness-cli story complete`/`update` for US-115 with proof booleans.
- Then `superpowers:finishing-a-development-branch`.

## Constraints / gotchas (not in the plan)

- Add `next-env.d.ts` to `frontend-mvp/.gitignore` (Next regenerates it; do not commit). `*.tsbuildinfo` is already ignored.
- `playwright.config.ts` must set `NEXT_PUBLIC_ADVISOR_MODE=mock` on the webServer and `reuseExistingServer`. First run needs `npx playwright install chromium`.
- Harness/build-gate is already satisfied (US-115 recorded, lane=normal). Do not re-run intake.
- Project AGENTS.md: no `Co-Authored-By` in commits; append AI session-log entries; keep progress only in `THANH-NOW.md`.
- Ignore the unrelated dirty files in `git status` (`.agent/skills/`, `.tokensave/`, `.agents/skills/`, other session logs) — not part of this work.

## References (do not duplicate — read these)

- Plan (authoritative, verbatim code): `docs/superpowers/plans/2026-07-17-frontend-mvp.md` — Task 9 §1803, Task 10 §1967, Task 11 §2059, Self-Review §2087.
- Design spec: `docs/superpowers/specs/2026-07-17-frontend-mvp-design.md`.
- Contract source: `ARCHITECTURE.md` §5.5–5.6, §7–8.
- Story: `docs/stories/epics/E01-air-conditioner-advisor-m1/US-115-approved-mock-first-frontend.md`.
- Session log: `ai-logs/dinh-nhat-thanh/sessions/2026-07-17T11-25-04Z_claude-code_950db6ec.md`.

## Suggested skills

- `superpowers:executing-plans` — resume Task 9 commit → 10 → 11 (or `superpowers:subagent-driven-development` since subagents are available and the plan recommends it).
- `superpowers:systematic-debugging` — for the `next build` OOM if the version bump does not resolve it.
- `context7-mcp` — fetch current Next.js 15 docs to pick the exact node-24-compatible patched version.
- `superpowers:verification-before-completion` then `superpowers:finishing-a-development-branch` — before closing out.
