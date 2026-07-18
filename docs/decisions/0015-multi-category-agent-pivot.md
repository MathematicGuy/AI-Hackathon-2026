# 0015 Multi-Category Agent Pivot

Date: 2026-07-18

## Status

Accepted

## Context

The partner problem statement spans the retailer's full catalog. Real data has
landed at `data/dataset/`: `Spec_cate_gia.xlsx` with 14 category sheets
(~8,700 products; mirror columns `model_code`/`sku`/`productidweb`/
`category_code`/`brand_id`/`brand`, Vietnamese spec columns that map 1:1 to the
future Postgres `products.attributes` JSONB keys, and `giá gốc`/
`giá khuyến mãi`/`khuyến mãi quà`), five policy markdown documents, and sample
chats from the retailer's previous bot. The data owner (Lưu Tiến Duy) may move
or re-format the storage later, but the logical format (tables, columns, rows)
is committed.

The product owner (Cường, 2026-07-18) directed: the sales agent must be able to
sell **every** product category, with no single-category specialization. The
Milestone 1 air-conditioner vertical (frozen contracts, AC ranking, synthetic
fixtures, and their test suite) is reclassified as a **mock/evaluation rig** —
kept intact and green for demonstration and regression, but no longer the
product direction.

## Decision

1. The product direction is a **multi-category, read-only, proactive sales
   agent** covering the 14 real categories, implemented under
   `backend/app/agent/` (epic `E02-multi-category-agent`, story IDs `US-2xx`).
2. For the agent, this decision supersedes the category-scope rule of ADR-001
   ("one category only: máy lạnh"). ADR-001 continues to govern the M1
   air-conditioner rig only.
3. The M1 artifacts (contracts, domain engine, fixtures, tests) are retained
   unchanged as the evaluation/demo rig; E02 must not break them.
4. The agent consumes real data through a swappable dataset adapter whose
   record shape mirrors the committed logical format (mirror keys + original
   attribute keys + price/promotion fields), so replacing Excel with the future
   database changes only the adapter and configured path.
5. The single-agent constrained-graph architecture is retained (no multi-agent
   supervisor): deterministic tools and validation around routed LLM calls
   (environment-owned `main`/`extraction`/`fallback`/`judge` routes per
   ADR-007).

## Alternatives Considered

1. Extend the frozen M1 AC pipeline category-by-category — rejected: the AC
   schemas are deeply category-specific; the product owner reclassified them as
   mock.
2. Multi-agent supervisor/specialist topology — rejected for M-scope:
   higher latency/cost/failure surface with no benefit over a constrained
   graph with deterministic tools.

## Consequences

Positive: the agent matches the problem statement and real data; the adapter
boundary de-risks the future database swap; the M1 rig remains a regression
harness.

Tradeoffs: generic (attribute-dict) product handling replaces deep typed
per-category models; deep deterministic ranking exists only in the AC rig for
now, while the agent uses simpler deterministic filtering/sorting plus
promotion-aware comparison.

## Follow-Up

- E02 stories US-201–US-206 implement the agent (catalog, tools, policy
  engine, conversation, salesman behavior, graph/API).
- The input-guardrail scope configuration must treat all 14 categories as
  in-scope for the agent while keeping the M1 rig's behavior unchanged.
