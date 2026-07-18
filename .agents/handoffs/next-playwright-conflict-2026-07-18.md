# Handoff — Next.js / Playwright dependency conflict

## Focus

Correct Task 9's dependency resolution so the frontend uses a Node 24-compatible, patched Next.js 15 release and the Next/Playwright advisories are actually removed. Work on branch `agent/m1-implementation` in `E:\VIN-INTERNSHIP\AI-Hackathon-2026`.

## Current state

- Task 9 base: `e251c31f6b2746fca19ab594c0cc6ce43b6f9f1d`.
- Task 9 commit needing correction: `9269034458f5038bf5b97db4d68ab69a1d40ed71`.
- The chat shell/page implementation in that commit matches the authoritative plan and must remain unchanged.
- The commit pins Next `15.1.12`, but fresh `npm audit --json` proves that release remains affected by critical/high/moderate Next advisories. Npm's non-major fix is Next `15.5.20`.
- A normal install of Next `15.5.20` conflicts with the plan's Playwright `1.49.1` because Next requires optional peer `@playwright/test ^1.51.1`.
- Npm audit independently flags Playwright `1.49.1` as high severity and recommends `@playwright/test 1.61.1`.
- A `--legacy-peer-deps` attempt was explicitly rejected; final dependency resolution must use normal npm behavior.
- The prior Next `15.1.0` OOM was not reproduced in this session. Do not claim the dependency bump proved that root cause.

## Authoritative artifacts

- Full task requirements: `.superpowers/sdd/task-9-brief.md`.
- Existing implementation report: `.superpowers/sdd/task-9-report.md`; append a correction section with fresh evidence.
- Original continuation context: `.agents/handoffs/frontend-mvp-continuation-2026-07-18.md`.
- Plan: `docs/superpowers/plans/2026-07-17-frontend-mvp.md` (Global Constraints and Task 9 only).
- Story: `docs/stories/epics/E01-air-conditioner-advisor-m1/US-115-approved-mock-first-frontend.md`.

## Required correction

1. Pin exact `next` `15.5.20`.
2. Pin exact `@playwright/test` `1.61.1` so Next's peer resolves normally and Playwright's advisory is removed.
3. Keep exact `react` and `react-dom` `19.0.0`.
4. Run a normal npm install with no legacy/force flags and commit the regenerated lockfile.
5. Update the plan's dependency-deviation note to explain the audit evidence and compatible Playwright bump; retain the non-reproduced OOM caveat.
6. Do not change chat/page behavior or broaden into unrelated Vitest/Vite/PostCSS upgrades. Report remaining advisories explicitly.
7. Create a follow-up Task 9 correction commit; do not rewrite or drop the existing Task 9 commit.

## Verification

From `frontend-mvp/` run and record:

- `npm list next react react-dom @playwright/test`
- `npm run typecheck`
- `npm run test`
- `npm run build`
- `npm audit --json`

The dependency tree must be clean; typecheck, 14 unit tests, and production build must pass on Node 24.16.0. The audit must contain no direct Next advisory objects and no `@playwright/test` or `playwright` vulnerability entries. A residual moderate `next` aggregate is acceptable only when it is solely caused by Next 15.5.20's hard dependency on PostCSS 8.4.31; document that upstream chain and do not add an override. Remaining unrelated advisories must be reported, not silently fixed.

Run `git diff --cached --check` and verify only the correction's required package, lockfile, plan-note, and report-related scope is staged. Preserve unrelated dirty `.agent/`, `.agents/skills/`, `.tokensave/`, AI log, and handoff files.

## Reporting

Append the correction report to `.superpowers/sdd/task-9-report.md` with the covering commands, exact outcomes, audit result, final commit, staged-scope check, and concerns. Return only status, commits, a one-line verification summary, and concerns.

## Suggested skills

- `superpowers:systematic-debugging` — treat audit and peer-resolution evidence as the root-cause inputs.
- `context7-mcp` — verify current framework/package compatibility if metadata is unclear.
- `superpowers:test-driven-development` — use the failing audit/normal-install checks before the dependency correction.
- `superpowers:verification-before-completion` — require fresh evidence before reporting done.
