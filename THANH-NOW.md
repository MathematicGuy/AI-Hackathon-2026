# Current Mission

## Demo promise

Vietnamese customer asks:

> Em muốn mua máy lạnh dưới 20 triệu cho phòng 18m², tiết kiệm điện, ít ồn.

MVP returns deterministic role winners from the synthetic M1 catalog, with evidence and no invented product facts.

## Current milestone

Milestone 1: complete M1.0 contract freeze, then build M1.1–M1.4 foundations into the M1.5 vertical slice. Current sprint deadline: **2026-07-17 13:47 UTC**.

## Owner focus

- Thành — AI/Eval planning and M1 evaluation-data contract.
- Team — assign M1.1 catalog, M1.2 decision engine, M1.3 guardrails, and M1.4 state/routing owners.

## Frozen evaluation contract

- Dataset: `data/aircon-m1-test-data/` only. Do not use `data-template-enriched.json` for M1.
- Catalog: 14 synthetic products in `aircon-m1-catalog-enriched.json`; never present them as live Điện Máy XANH facts.
- Evaluation: 26 JSONL cases in `aircon-m1-eval-cases.jsonl`; validate with `aircon-m1-data-validation.json` before runs.
- Golden regression: `AIRCON-M1-001` must produce Best Overall `AC-M1-002`, Best Value `AC-M1-003`, and Cheapest Qualified `AC-M1-006`.

## Active work

- M1.0 — freeze request, response, state, product, and graph contracts.
- M1.9 / US-117 — implement dataset loader, deterministic assertions, Langfuse import, and release report when selected.

## Working files

- `PROJECT_MANAGEMENT.md` — milestone plan, evaluation tasks, proof expectations.
- `docs/stories/backlog.md` — US-117 candidate only; no active story packet yet.
- `data/aircon-m1-test-data/` — committed evaluation fixtures; inspect, do not treat as production catalog data.

## Blockers and risks

- No active M1 story packet or evaluation runner exists yet.
- Ranking fixture is test-only; production ranking policy still needs approval.
- Keep `resources/` out of scope unless explicitly requested.

## Next integration checkpoint

- Create selected M1 story packets and durable Harness story records.
- Prove M1.0 contracts, then start M1.1–M1.4 in parallel.
