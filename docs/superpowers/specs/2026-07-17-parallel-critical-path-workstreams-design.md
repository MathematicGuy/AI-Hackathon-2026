# Parallel Critical-Path Workstreams Design

> **Legacy provenance artifact:** Retained for historical context. It is not
> current authority. Follow `docs/README.md` and do not add new files under
> `docs/superpowers/`.

## Goal

Let three developers advance the four M1 foundation lanes concurrently without sharing a working tree, duplicating story ownership, or merging unreviewed work.

## Ownership

| Controller / workstream | Stories | Dependency order | Scope |
| --- | --- | --- | --- |
| Thành | US-107 → US-108 → US-109 → US-110 | Sequential after completed US-106 | Normalization, evidence, constraints, ranking, and truthful display selection |
| USER1 | US-102 → US-103 | US-102 starts from completed US-121; US-103 starts after US-102 | Input guardrails, intent classification, and need extraction |
| USER2 | US-104 → US-105 | US-104 starts from completed US-121; US-105 starts only after both US-103 and US-104 are merged | State merge, clarification, routing, and persistence |

The controller retains M1.5 integration ownership. USER1 and USER2 do not start later stories unless the controller explicitly reallocates them.

## Isolation and file boundaries

Each workstream uses its own branch and worktree or clone. Concurrent implementation in the same working tree is prohibited.

- USER1 branch: `agent/user1-m1-3-guardrails-intent`
- USER2 branch: `agent/user2-m1-4-state-routing`
- Thành continues on `agent/m1-implementation`.

USER1 owns the files listed by Tasks 6 and 7 in `docs/superpowers/plans/2026-07-17-m1-1-through-m1-8.md`. USER2 owns the files listed by Tasks 8 and 9. Neither teammate edits Thành's `backend/app/domain/air_conditioner/` decision-engine files, shared contracts, or another user's NOW ledger unless a reviewed dependency requires a narrowly scoped merge-conflict fix.

## Story and progress protocol

Each worktree activates only its current story packet, follows RED → GREEN TDD, receives a separate task review, records Harness proof and a trace, and commits only story-owned files. Ignored Harness databases remain local to each worktree.

- `docs/team/now/THANH-NOW.md` is the controller and integration ledger.
- `docs/team/now/USER1-NOW.md` tracks USER1's assigned work only.
- `docs/team/now/USER2-NOW.md` tracks USER2's assigned work only.
- A teammate updates only their own NOW file. The controller updates
  `docs/team/now/THANH-NOW.md` after reviewed merges.
- Do not create `PROGRESS.md` or `.superpowers/sdd/progress.md`.

## Merge sequence

1. USER1 completes, reviews, traces, and submits US-102.
2. USER2 completes, reviews, traces, and submits US-104 independently; the controller may merge US-102 and US-104 in either order.
3. USER1 refreshes from main, then completes US-103.
4. After US-103 and US-104 are both on main, USER2 refreshes from main and completes US-105.
5. Thành serially integrates reviewed foundation commits. M1.5 starts only after US-105 and US-107 through US-110 are merged and their proof is current.

Every merge must preserve the frozen M1 contract and pass the story's focused verification plus contract tests where required.

## Coordination failure handling

- If a branch needs a shared contract change, stop and route the decision to Thành before editing.
- If a planned file is already changed by another workstream, stop and reassign ownership before implementation.
- If US-103 is delayed, USER2 keeps US-105 blocked rather than implementing against an unmerged interface.
- Model labels are requests only: context investigation requests `gpt-5.6-luna-high`; code implementation requests `gpt-5.6-terra-high`. Do not claim runtime enforcement when the API cannot select a model.

## Acceptance criteria

- Root-level USER1 and USER2 ledgers name exact stories, prerequisites, file boundaries, tests, branch names, and handoff conditions.
- `docs/team/now/THANH-NOW.md` shows delegated ownership without duplicating
  teammate task details.
- No story has two active owners.
- The split keeps all three developers productive before M1.5 while respecting US-105's dependency on US-103 and US-104.
