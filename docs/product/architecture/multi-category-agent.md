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

Single-agent constrained graph (no multi-agent supervisor). The agent's
reasoning core is **gpt-4o-mini via `OPENAI_API_KEY`** (Cường's direction,
2026-07-19; override with `AGENT_MAIN_LLM_MODEL`), with OpenRouter deepseek
and Mistral as automatic fallbacks and a deterministic keyword fallback when
no LLM answers. The extractor sees the full session context: current need,
asked questions, the pending question's text, and the last three exchanges.
Deterministic code owns filtering, comparison, validation, and quoting.
(M1 keeps its own deepseek rule — unchanged.)

## 2. Runtime flow

```text
guard → understand → merge_need → route
   route = clarify           (bundled cold-start opener 2-3 questions, then 1/turn)
         | product_flow      (search/aggregate/compare/detail tools → sell)
         | policy_flow       (corpus retrieve → natural answer, verbatim-validated)
         | catalog_overview  (category menu / per-category aggregate overview)
         | price_range_flow  (aggregate price_min/max for the category)
         | promotion_flow    (grounded promo overview or graceful degradation)
         | smalltalk         (friendly employee reply + gentle sales pivot)
         | product_qa        (deep Q&A over presented products / metric transparency)
         | stop | scope_safe
→ sell (proactive salesman prose over verified records + promotions)
→ validate (grounding: claims ⊆ records; quotes ⊆ corpus; question cap)
→ respond (+ session state persist)
```

## 3. Data layer (dual-backend: Duy's Postgres + Excel fallback)

- **Backend selection** (`default_adapter()`): the agent prefers the Postgres
  data platform (`products` table from `backend/migrations/0002_catalog.sql`,
  connected through `backend.app.db.connection`) and falls back to
  `ExcelDatasetAdapter` (`AGENT_DATASET_PATH`, default
  `data/dataset/Spec_cate_gia.xlsx`) when the database is unreachable or not
  configured. `AGENT_DATA_BACKEND=excel|postgres` forces a backend.
- Record shape is identical from both backends: mirror keys (`model_code`,
  `sku`, `productidweb`, `category_code`, `brand_id`, `brand`) + `attributes`
  dict preserving the ORIGINAL Vietnamese column names/values + parsed
  `list_price`, `sale_price`, `gift_promotion`. Note from the platform schema:
  `sku` is the unique business key; `productidweb` may be shared by variants.
- `CategoryRegistry`: 14 categories — sheet name, `category_code`, Vietnamese
  detection markers, attribute keys per category.
- **Measured data notes** (re-audited 2026-07-18 evening): the Máy giặt sheet
  NOW carries specs (Khối lượng tải ~70%, kiểu cửa 77%, tốc độ vắt 53% —
  the earlier "no spec columns" note is stale and retired); parsable price
  coverage is 14–72% per category; there is no stock column (the agent
  answers availability honestly). Placeholder values ("Hãng không công bố",
  "Đang cập nhật", "Không"...) are filtered everywhere a spec is parsed —
  the bot never claims a spec the maker did not publish.
- **Dimension registry** (`catalog/dimensions.py`, evidence-based per the
  field-profile audit): each category declares its important dimensions —
  key, kind (numeric higher/lower, ordinal like Độ phân giải FHD<QHD<UHD,
  enum-info, feature), unit, a thang-đo explanation, and the preference
  keywords that point at it. Semi-independent per ngành: a category's
  dimension list evolves without touching the graph.

## 4. Preference memory (fixed format, in-session)

`GenericNeed` is the single fixed format for preferences/requirements:
`category_code?, usage_purpose?, budget_min?, budget_max?, brand_prefs[],
priorities[], attribute_constraints{}, location?`.

Update modes:

1. **Incremental patch-merge** — explicit values win, omitted fields persist,
   explicit null is not deletion (US-104 semantics).
2. **Rewrite on change-of-mind** — a correction replaces the stated value
   immediately ("nâng lên tầm 20-25 triệu" overrides the old window).
3. **Explicit clear** (round 4) — removals travel on
   `AgentUnderstanding.clear_fields` because merge semantics cannot delete:
   "không tra trong mức đó nữa"/"bỏ giới hạn giá"/"khoảng giá khác" clears
   budget_min+budget_max and un-answers the budget question so the bot asks
   for the new range; numbers inside old-reference phrases are never
   re-parsed as a new budget.
4. **Reset on category/shopping-intent switch** — the current need is archived
   to `previous_needs[]` (recoverable when the user returns to that category),
   a fresh need starts for the new category and re-triggers that category's
   cold-start script; explicit session-wide preferences (brand, location)
   carry over; shown/rejected lists are per category.

## 5. Cold-start clarification

Per-category question scripts live in versioned data
(`conversation/scenario_data.py`), ordered by material impact — budget is
never the first question (e.g. PC: purpose → budget; tủ lạnh: household size →
budget → door style; máy lạnh: room size → budget → priority) — with
purpose-aware follow-ups once the usage purpose is known (gaming →
display/GPU). Rules: when a category cycle starts, the opener bundles the top
2-3 script questions into one message (① ② ③) so the customer answers in one
go — the whole bundle is marked asked and the first question stays pending
for plain-reply capture; later follow-ups ask one question per turn. A single
multi-part reply answering several bundled questions at once ("24-27 inch,
làm việc, xem phim, tầm 3-5 triệu") is captured in full: the extractor fills
size/purpose/budget in one patch, and the deterministic fallback extracts
inch sizes for screen categories plus budget/purpose from the whole message. Never
re-ask an answered or already-asked question, and proceed with tools as soon
as the material minimum (category + one narrowing fact) is known. A plain
reply to the pending question is captured verbatim into the fixed-format need
(`attribute_constraints[question_key]`) as per-category filter memory, and a
materially new search reopens the clarification cycle. Per-category domain
rules (`conversation/domain_rules.py`) turn captured answers into concrete
deterministic filters where the data supports it (household size → capacity
band, room area → coverage range, screen size → inches).

## 6. Policy engine (ADR-0016)

Markdown corpus from `AGENT_POLICY_DIR` (default `data/dataset`), heading-based
sections, keyword-scored retrieval with a relevance floor (`min_score` — a
weak top match degrades gracefully instead of quoting an off-topic clause),
no vector store. Lazy: loaded only for `policy_question` intent or a
compliance check. Every policy answer quotes the source **verbatim**
(validated as an exact substring) but presents it naturally: "Dạ theo
{display name} của bên em ạ: …" using the human-readable policy name
(`answer.DISPLAY_NAMES` / `display_source()`) — file names never appear, and
the literal “trích nguyên văn: "…"” frame is used only when the customer
explicitly asks for a verbatim quote ("nguyên văn"/"trích"). Requests
conflicting with policy get a sincere apology + the governing clause +
legitimate alternatives; a failed quote validation, by contrast, is OUR
retrieval problem and degrades to a graceful no-info answer, never the
violation apology. Corpus hardening (round 2): conversation-generic folded
words (mục/đích/sử/dụng) are stopwords so an echoed question cannot match the
data-privacy headings, and windowed chunks never end on an orphan enumeration
marker ("b."). Policy always outranks sales behavior.

## 7. Proactive salesman behavior

Tone: polite retail Vietnamese ("Dạ… ạ") learned from the sample chats, but
proactive rather than passive. Suggestion roles are **preference-driven over
the dimension registry** (2026-07-19 round 3): with no preference signal the
classic trio holds (best price / best value / headline-dimension pick); when
the captured need names dimensions ("chơi game" → Thời gian đáp ứng, "êm" →
Độ ồn), up to two dimension roles replace the generic performance pick — and
every role badge carries its evidence value ("[Sắc nét nhất: QHD (2560 x
1440)]", "[Card mạnh nhất: 8 GB GDDR6]") so the metric is transparent. A
dimension role is skipped when under 30% of the pool has real data for it.
Explicit customer roles ("rẻ nhất" → best_price, "đắt nhất" →
most_expensive) always win, and answer over the whole pool (a role ask may
re-show a model already presented). Answers then add a grounded "Ngoài ra
anh/chị có thể tham khảo thêm" section (≤3 extra models with
price/promotion), surface
`giá khuyến mãi`/% giảm/`khuyến mãi quà`, and ends with at most one
consultative question. Comparison output always includes the promotion delta,
not just specs. An optional LLM polish pass (env `AGENT_LLM_POLISH=1`) may
rephrase the deterministic text; the grounding validator re-checks the
polished text and falls back to the deterministic version on any violation.
Prohibited (kept from M1): invented scarcity/urgency, pushing an expensive
product without a customer benefit, repeating an answered question, continuing
after stop, and any claim not present in retrieved records. The bot never
creates, commits, or acknowledges promotions beyond the data — benefit-exploit
attempts ("giảm thêm cho mình", "bạn đã hứa…") get a fixed polite refusal
before any content processing (`promotion_exploit_blocked`).

## 8. Guardrails

Input: refusal fires ONLY on deliberate abuse — the word limit, deterministic
payload rules (prompt injection, credential/hidden-prompt, unsafe execution),
a real NeMo block, and promotion-exploit attempts. Ordinary text without
shopping markers is never refused (`degraded_fail_closed` does not fire for
the agent): friendliness is handled at the understanding layer, matching the
retailer's real bot. The M1 rig's stricter default behavior is untouched.
Output: deterministic grounding validation — product IDs/prices/promotions
must exist in retrieved records, policy quotes must be verbatim, at most one
question per suggestion/comparison answer (the bundled cold-start opener may
carry 2-3); a failed check strips the claim and degrades to verified facts.
User-need amounts (budgets) render as "X triệu" so they are never mistaken
for price claims.

## 9. Intents (agent enum, 15 values)

`new_search, change_constraints, more_recommendations, compare_products,
product_detail, check_availability, policy_question, catalog_overview,
price_range_query, promotion_inquiry, smalltalk, question_clarification,
product_qa, stop, unsupported`.

Round-3 note (2026-07-19): `product_qa` answers deep questions about the
products just presented and about the bot's own measures ("cái nào tốt hơn
về mặt hiệu năng?", "thang đo là gì?", "màn nào nét hơn?") — it explains the
category's thang đo transparently and compares the presented models
dimension-by-dimension with real record values, honestly disclosing "hãng
không công bố" where data is missing. It takes precedence over
question_clarification. Comparison (`_compare_flow`) gained the same
dimension table with per-axis verdicts.

Round-4 note (2026-07-19): comparison is tool-driven even with nothing
presented yet — "So sánh 2 mẫu máy lạnh rẻ nhất"/"nổi bật" fetches its own
pair (cheapest / priciest / deepest-discount qualifiers, budget-aware) and
compares immediately; the pair becomes `last_presented_ids` so deep
follow-ups chain. Bare agreements ("ok", "ừ") are exact-match small talk —
no message-length limit exists at any layer (frontend or backend).

Routing notes (2026-07-19 live-test round): price-range and running-promotion
questions are catalog questions answered from the aggregate tool (never
policy); catalog exploration ("bán cái gì", "có những loại hàng nào") returns
the category menu or a per-category overview; small talk (thanks, weather,
greetings, polite agreement) gets a friendly employee-style reply with a
gentle sales pivot — never a refusal.

Round-2 notes (2026-07-19): understanding is **state-aware** — the
deterministic fallback receives the active category, so a mid-consultation
follow-up that matches no marker ("máy đắt nhất đi em") continues the product
flow instead of dumping the menu; "đắt nhất/xịn nhất" maps to the
`most_expensive` suggestion role. An echo of the bot's own question ("mục
đích sử dụng tủ lạnh á?") routes to `question_clarification`: the bot explains
its question with a per-category example (never policy, never captured as the
answer). Products the catalog does not carry (laptop, điện thoại, tivi…) get
an honest "bên em hiện chưa kinh doanh X" plus the closest in-catalog
alternatives. Money parsing tolerates live-chat typos (trịu/trieu/tr/củ).
ReAct assessment: the round-2 misroutes all traced to a dead/weak extractor
falling back to a stateless keyword router — fixed by the gpt-4o-mini-first
extractor with full conversation context plus the state-aware fallback; a
dynamic ReAct loop stays deferred until tools with side effects (stock,
ordering) arrive.

## 10. Repository mapping

```text
backend/app/agent/
├── contracts.py                # AgentIntent, GenericNeed, AgentState, AgentResponse
├── catalog/{dataset_adapter,registry,promotions,dimensions}.py
├── tools/{search,aggregate,compare,detail}.py
├── policies/{corpus,answer}.py
├── conversation/{coldstart,memory}.py + scenarios.yaml
├── llm/client.py               # env-routed OpenAI-compatible client (main→fallback)
├── prompts/*.md                # SOUL, SALES_POLICY, POLICY_QA, CLARIFY (Vietnamese)
├── graph.py                    # LangGraph assembly
├── api.py                      # POST /api/v1/agent/respond (+ /respond/stream NDJSON)
└── demo.py                     # local CLI chat
```

`/respond/stream` is presentation streaming: the deterministic pipeline
produces the full grounded text, which is then chunk-streamed as NDJSON
(`{"type":"chunk"}`… then `{"type":"done"}` with intent/flags). Token-level
streaming arrives when the sell step itself runs on a streaming LLM.
`POST /api/v1/agent/feedback` records like/dislike per assistant message
(in-memory + server log; Langfuse hookup deferred with the judge wiring).
Session memory write-throughs to JSON per session (`AGENT_SESSION_DIR`,
default `data/agent-sessions/`): the fixed-format need, per-category
archives, asked/shown lists, pending question — inspectable on disk and it
survives restarts; corrupt or missing files never break a turn (best-effort,
in-process state stays primary).
Frontend edit is replay-based: editing a user message cuts the conversation
back to that point and silently replays the earlier user turns on a fresh
session before sending the edited text — real edit semantics over the
in-process session store. The bot self-addresses as "em" in every UI string.

Stories: `docs/stories/epics/E02-multi-category-agent/` (US-201 catalog,
US-202 tools, US-203 policy, US-204 conversation, US-205 salesman, US-206
graph/API/demo).
