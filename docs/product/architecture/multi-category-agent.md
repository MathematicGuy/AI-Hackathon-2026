# Multi-Category Sales Agent Architecture (E02)

> **Status:** Accepted direction per ADR-0015/ADR-0016 (2026-07-18)
> **Scope:** All 14 real product categories in `data/dataset/Spec_cate_gia.xlsx`
> **Primary language:** Vietnamese
> **Relation to M1:** The air-conditioner M1 pipeline is a mock/evaluation rig
> (ADR-0015); this document is the authoritative architecture for the product
> agent. Model routing follows ADR-007 (environment-owned routes).
> **Namespace:** `backend/app/agent/` — fully separate from the M1 rig files.

## 1. What the agent is

A Vietnamese, read-only, **proactive sales advisor** for the retailer's full
catalog. It understands a customer's real need, asks the missing cold-start
questions for the requested category, narrows the search space with
deterministic tools, recommends and compares products with promotions
front-and-center, answers policy questions with verbatim quotes, and always
pushes toward a helpful sale — without ever inventing a price, spec, stock,
promotion, or policy clause.

Single-agent constrained graph (no multi-agent supervisor). LLM calls are
routed via the environment-owned `main`/`extraction`/`fallback` routes;
deterministic code owns filtering, comparison, validation, and quoting.

## 2. Runtime flow

```text
guard → understand → merge_need → route
   route = clarify        (cold-start question for the category, 1/turn, ≤3/cycle)
         | product_flow   (search/aggregate/compare/detail tools → sell)
         | policy_flow    (corpus retrieve → answer with verbatim quote)
         | stop | scope_safe
→ sell (proactive salesman prose over verified records + promotions)
→ validate (grounding: claims ⊆ records; quotes ⊆ corpus; ≤1 question)
→ respond (+ session state persist)
```

## 3. Data layer (swap-ready for Duy's database)

- `ExcelDatasetAdapter` reads `AGENT_DATASET_PATH` (default
  `data/dataset/Spec_cate_gia.xlsx`) once and caches records.
- Record shape mirrors the committed logical format and the future
  `products` table: mirror keys (`model_code`, `sku`, `productidweb`,
  `category_code`, `brand_id`, `brand`) + `attributes` dict preserving the
  ORIGINAL Vietnamese column names/values + parsed `list_price`, `sale_price`,
  `gift_promotion`.
- Swapping to Postgres later = new adapter + path/config change only. Tools
  and conversation code never read Excel directly.
- `CategoryRegistry`: 14 categories — sheet name, `category_code`, Vietnamese
  detection markers, attribute keys per category.

## 4. Preference memory (fixed format, in-session)

`GenericNeed` is the single fixed format for preferences/requirements:
`category_code?, usage_purpose?, budget_min?, budget_max?, brand_prefs[],
priorities[], attribute_constraints{}, location?`.

Three update modes:

1. **Incremental patch-merge** — explicit values win, omitted fields persist,
   explicit null is not deletion (US-104 semantics).
2. **Rewrite on change-of-mind** — a correction replaces the stated value
   immediately.
3. **Reset on category/shopping-intent switch** — the current need is archived
   to `previous_needs[]` (recoverable when the user returns to that category),
   a fresh need starts for the new category and re-triggers that category's
   cold-start script; explicit session-wide preferences (brand, location)
   carry over; shown/rejected lists are per category.

## 5. Cold-start clarification

Per-category question scripts live in versioned data
(`conversation/scenarios.yaml`), ordered by material impact (e.g. laptop:
purpose → budget; tủ lạnh: household size → budget → door style; máy lạnh:
room size → budget → priority). Rules: one question per turn, at most three per
cycle, never re-ask an answered question, proceed with tools as soon as the
material minimum (category + one narrowing fact + budget) is known.

## 6. Policy engine (ADR-0016)

Markdown corpus from `AGENT_POLICY_DIR` (default `data/dataset`), heading-based
sections, keyword-scored retrieval, no vector store. Lazy: loaded only for
`policy_question` intent or a compliance check. Every policy answer carries a
**verbatim quote** (validated as an exact substring of the source) plus the
source document name. Requests conflicting with policy get a sincere apology +
the governing clause + legitimate alternatives. Policy always outranks sales
behavior.

## 7. Proactive salesman behavior

Tone: polite retail Vietnamese ("Dạ… ạ") learned from the sample chats, but
proactive rather than passive: every useful answer suggests a concrete next
step, surfaces `giá khuyến mãi`/% giảm/`khuyến mãi quà`, frames benefits in the
customer's terms, and ends with at most one consultative question. Comparison
output always includes the promotion delta, not just specs. Prohibited (kept
from M1): invented scarcity/urgency, pushing an expensive product without a
customer benefit, repeating an answered question, continuing after stop, and
any claim not present in retrieved records.

## 8. Guardrails

Input: the layered guardrail (word count → regex/payload → NeMo rail → scope)
is reused with an agent scope configuration in which all 14 categories are
in-scope; injection/credential/unsafe-execution rules unchanged; the M1 rig's
default behavior is untouched. Output: deterministic grounding validation —
product IDs/prices/promotions must exist in retrieved records, policy quotes
must be verbatim, at most one question; a failed check strips the claim and
degrades to verified facts.

## 9. Intents (agent enum, 9 values)

`new_search, change_constraints, more_recommendations, compare_products,
product_detail, check_availability, policy_question, stop, unsupported`.

## 10. Repository mapping

```text
backend/app/agent/
├── contracts.py                # AgentIntent, GenericNeed, AgentState, AgentResponse
├── catalog/{dataset_adapter,registry,promotions}.py
├── tools/{search,aggregate,compare,detail}.py
├── policies/{corpus,answer}.py
├── conversation/{coldstart,memory}.py + scenarios.yaml
├── llm/client.py               # env-routed OpenAI-compatible client (main→fallback)
├── prompts/*.md                # SOUL, SALES_POLICY, POLICY_QA, CLARIFY (Vietnamese)
├── graph.py                    # LangGraph assembly
├── api.py                      # POST /api/v1/agent/respond
└── demo.py                     # local CLI chat
```

Stories: `docs/stories/epics/E02-multi-category-agent/` (US-201 catalog,
US-202 tools, US-203 policy, US-204 conversation, US-205 salesman, US-206
graph/API/demo).
