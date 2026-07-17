# Current Mission

## Demo promise

Vietnamese customer asks:

> Em muốn mua máy lạnh dưới 20 triệu cho phòng 18m², tiết kiệm điện, ít ồn.

MVP returns deterministic role winners from the synthetic M1 catalog, with evidence and no invented product facts.

## Current milestone

Milestone 1: M1.0 contract freeze is complete; build M1.1–M1.4 foundations into the M1.5 vertical slice. Current sprint deadline: **2026-07-17 13:47 UTC**.

## Owner focus

- Đinh Nhật Thành — M1.1–M1.8 execution controller and contract owner.
- Context investigation assignments request `gpt-5.6-luna-high`; code implementation assignments request `gpt-5.6-terra-high`. The current subagent API cannot enforce model selection, so these are requested labels, not verified runtime models.

## M1.1–M1.8 delegated execution board

| Order | Milestone / stories | Delegated role | Requested model | Depends on | Status |
| ---: | --- | --- | --- | --- | --- |
| 0 | Contract reconciliation / US-121 | Fresh implementation subagent, then separate reviewer | `gpt-5.6-terra-high` | US-100 | ✅ Done — 8 tests, review approved, trace 11 |
| 1 | M1.1 / US-106 catalog pagination | Fresh implementation subagent, then separate reviewer | `gpt-5.6-terra-high` | US-121 | ✅ Done — 53 tests, review approved, trace 12 |
| 2 | M1.1 / US-107 normalization and evidence | Fresh implementation subagent, then separate reviewer | `gpt-5.6-terra-high` | US-106 | 🟨 Ready to activate |
| 3 | M1.3 / US-102 layered input guardrail | Fresh implementation subagent, then separate reviewer | `gpt-5.6-terra-high` | US-121 | ⬜ Queued |
| 4 | M1.3 / US-103 Vietnamese intent/need extraction | Fresh implementation subagent, then separate reviewer | `gpt-5.6-terra-high` | US-102 | ⬜ Queued |
| 5 | M1.4 / US-104 state merge and correction precedence | Fresh implementation subagent, then separate reviewer | `gpt-5.6-terra-high` | US-121 | ⬜ Queued |
| 6 | M1.2 / US-108 hard constraints | Fresh implementation subagent, then separate reviewer | `gpt-5.6-terra-high` | US-107 | ⬜ Queued |
| 7 | M1.2 / US-109 injected deterministic ranking | Fresh implementation subagent, then separate reviewer | `gpt-5.6-terra-high` | US-108 | ⬜ Queued; production policy remains injected |
| 8 | M1.2 / US-110 truthful deduplication | Fresh implementation subagent, then separate reviewer | `gpt-5.6-terra-high` | US-109 | ⬜ Queued |
| 9 | M1.4 / US-105 clarification/routing/persistence | Fresh implementation subagent, then separate reviewer | `gpt-5.6-terra-high` | US-103, US-104 | ⬜ Queued |
| 10 | M1.5 / US-101 + US-116 gateway, graph, trace | Fresh integration subagent, then separate reviewer | `gpt-5.6-terra-high` | US-105, US-106–US-110 | ⬜ Dependency-gated |
| 11 | M1.6 / US-111 + US-112 grounded output/fallback | Fresh integration subagent, then separate reviewer | `gpt-5.6-terra-high` | M1.5 | ⬜ Dependency-gated |
| 12 | M1.7 / US-113 + US-114 continuations | Fresh integration subagent, then separate reviewer | `gpt-5.6-terra-high` | M1.5 | ⬜ Dependency-gated |
| 13 | M1.8 / US-115 mock-first frontend | Fresh frontend implementation subagent, then separate reviewer | `gpt-5.6-terra-high` | US-121 mock contract | ⬜ Queued |
| 14 | M1.8 / US-115 real API E2E | Fresh frontend integration subagent, then separate reviewer | `gpt-5.6-terra-high` | M1.5–M1.7 | ⬜ Dependency-gated |

Detailed task scope, interfaces, RED/GREEN commands, and dependency order: `docs/superpowers/plans/2026-07-17-m1-1-through-m1-8.md`.

## Frozen evaluation contract

- Dataset: `data/aircon-m1-test-data/` only. Do not use `data-template-enriched.json` for M1.
- Catalog: 14 synthetic products in `aircon-m1-catalog-enriched.json`; never present them as live Điện Máy XANH facts.
- Evaluation: 26 JSONL cases in `aircon-m1-eval-cases.jsonl`; validate with `aircon-m1-data-validation.json` before runs.
- Golden regression: `AIRCON-M1-001` must produce Best Overall `AC-M1-002`, Best Value `AC-M1-003`, and Cheapest Qualified `AC-M1-006`.

## Active work

- M1.0 — request, response, state, product, graph, and model-routing contracts frozen with `US-100` proof.
- M1.1–M1.8 — implementation plan complete; US-121 and US-106 are complete, and US-107 is the only next story to activate. Later story packets remain uncreated until their dependency gate opens.
- M1.9 / US-117 — implement dataset loader, deterministic assertions, Langfuse import, and release report when selected.

## Integration status

- Completed US-100/US-121 scope committed on `agent/m1-implementation` as `8ce3b51` plus fixture proof `f551a2a`.
- Local `main` merged those commits as `bfc097c` and `07fbbc9`.
- Clean-main contract verification: 8 passed; third-party pytest plugin autoload was disabled because the global `deepeval` plugin attempted an out-of-scope filesystem write.

## Working files

- `PROJECT_MANAGEMENT.md` — milestone plan, evaluation tasks, proof expectations.
- `docs/stories/backlog.md` — US-117 candidate only; no active story packet yet.
- `data/aircon-m1-test-data/` — committed evaluation fixtures; inspect, do not treat as production catalog data.

## Blockers and risks

- Ranking fixture is test-only; production ranking policy still needs approval.
- Subagent model names are requested in prompts but cannot be enforced by the current delegation API.
- Keep `resources/` out of scope unless explicitly requested.

## Next integration checkpoint

- Activate US-107 only, complete RED → GREEN and separate review, then activate the next dependency-ready foundation story.
- Keep all later story packets uncreated until their turn in the dependency order.
