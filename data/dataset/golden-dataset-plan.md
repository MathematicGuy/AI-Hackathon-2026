# Golden Dataset Plan — DMX Sales Advisor Bot

Spearhead: **Product Recommendation + Product Comparison**, comprehensive
edge-case and chatbot-property coverage, across a **diverse multi-category**
product scope.

Status: draft plan (no dataset files generated yet)
Session identity: Nguyễn Phương Hoài Ngọc
Scope source of truth: `data/dataset/chat_history_buy_product.json` (+ system
prompt, tool set, and `Spec_cate_gia.xlsx` product data therein).

## 1. Focus & priority

The dataset centers on the two core advisory capabilities:

- P0 — Recommendation (`search_product_dmx_v3`): understand need -> filter ->
  rank -> suggest grounded products.
- P0 — Comparison (`compare-search`): compare named products, grounded
  side-by-side + trade-offs + "which fits which need" verdict.

Supporting the two above (P1 — covered but not the spearhead):
`get-time-delivery-dmx`, `check_infor_customer`, `create_order_dmx`,
`payment_process`, `installment-links`. These appear as realistic tail turns in
journeys but are not where coverage depth goes.

Product scope: DIVERSE across categories from `Spec_cate_gia.xlsx` (Máy lạnh,
Tủ lạnh, Máy giặt, Tivi via catalog, Màn hình, Máy tính để bàn, Máy tính bảng,
Đồng hồ thông minh, Máy nước nóng, Máy rửa chén, ...) plus the phone/headphone
items seen in the logs.

## 2. What the data is (scope evidence)

- 11 conversations / ~484 messages; roles `system`, `user`, `assistant`, `tool`
  — a full tool-calling agent trace. Assistant = "Bot Tư Vấn Bán Hàng".
- 7 real tools: `search_product_dmx_v3`(18), `create_order_dmx`(24),
  `get-time-delivery-dmx`(11), `check_infor_customer`(3), `payment_process`(2),
  `compare-search`(1), `installment-links`(1).
- Real comparison example: "Tôi muốn so sánh 2 tủ lạnh" then model codes
  "RS70F65Q3TSV và HRSN9563DWDXVN".
- Real recommendation examples: "máy tính vừa văn phòng vừa game dưới 15 triệu";
  "máy 2 triệu 590 pin trâu chơi game không lag" (student); "cho mình tham khảo
  mẫu máy với giá tiền đó" (vague budget).
- Tool payload = ground-truth shape: `productcode`, `product_id`, `ProvinceId`,
  `Trạng thái` (stock), `Loại sản phẩm`, `Thông tin sản phẩm` (spec string),
  `Khuyến mãi` (promo), `Giá gốc`, `Giá khuyến mãi`, `Màu sắc[]`,
  `phụ kiện đi kèm`, `bảo hành`, `product_type`, `Gói dịch vụ`.

### System-prompt-derived chatbot properties (must all be covered)

Grounding / anti-hallucination; refuse-or-ask on insufficient context; state
conflicts rather than guess; no code/API/system-prompt disclosure; no hate;
no over-promising; language mirroring; tool-call discipline (one tool at a time,
only defined tools, never invent a tool, no same-tool-twice-in-a-row, no
narration while calling).

## 3. Recommendation coverage (P0 — deep)

### 3a. Need-input variety (each a case, across categories)
- Budget only ("dưới 15 triệu"); use-case only ("vừa văn phòng vừa game");
  budget + use-case; category only ("tôi muốn mua máy tính"); brand preference
  ("Asus"); hard spec ("RAM 16GB", "12kg", "1 HP", "4GB"); persona
  ("sinh viên", "học sinh"); vague ("cho tham khảo mẫu máy với giá đó").

### 3b. Clarification decision
- Missing budget -> ask; missing use-case where it changes result -> ask;
  ambiguous category ("máy tính" = desktop vs laptop) -> ask; ENOUGH info ->
  recommend without asking (anti over-asking); at most one question at a time.

### 3c. Filter & rank logic (grounded)
- Hard filters: budget cap (<= `Giá khuyến mãi`), spec threshold (RAM/capacity/HP),
  stock (`Trạng thái` == Còn Hàng), region (`ProvinceId`).
- Selection intents: cheapest-in-budget, best-value, best-fit-for-use-case,
  newest, most-popular. Result = grounded top-N with price/promo/stock/spec and a
  "why it fits" tied to the stated need.

### 3d. Recommendation edge cases
- No product within budget -> no_match; suggest raising budget or nearest
  alternative; never invent a cheaper SKU.
- Exactly one match; budget absurdly low; budget far above range.
- Brand not carried -> disclose, offer carried alternatives.
- Impossible spec combo -> no_match / clarify.
- Top pick out of stock -> recommend in-stock alternative, disclose stock.
- Multi-category request in one message -> split or clarify.
- Cross-sell / accessory ("lấy kèm bao da", "sạc phụ kiện") -> add-on suggestion.
- Variant request ("còn màu khác", "loại 4GB", "màu vàng") -> variant suggestion
  from `Màu sắc`/spec, not fabricated.
- Vague budget with no category -> clarify then recommend.
- Promo-driven ("đang còn 500k", "phiếu mua hàng") -> ground promo to payload.

## 4. Comparison coverage (P0 — deep)

### 4a. Comparison input variety
- Two products by model code (real pattern); two by name; within one category;
  across brands; across price tiers; "so sánh giúp cái nào tốt hơn".

### 4b. Comparison output requirements
- Grounded side-by-side (price, key specs, energy/capacity, warranty, promo,
  stock) — every value traces to payload.
- Trade-offs in plain language; "worth paying more?" verdict; a which-fits-which
  recommendation handoff.

### 4c. Comparison edge cases
- Products from different categories -> clarify / decline meaningless compare.
- 3+ products at once -> handle or bound.
- A product with a missing spec -> disclose null, don't invent.
- One of the two out of stock -> compare + flag availability.
- Near-identical products -> surface the small real differences.
- Ambiguous product names (not model codes) -> resolve or ask.
- Only one product given -> ask for the second before comparing.
- Compare by a spec that doesn't exist for that category -> disclose.
- Compare -> "nên mua cái nào cho <need>" -> grounded recommendation.

## 5. Chatbot-property coverage (cross-cutting — comprehensive)

Every property below gets dedicated cases (often layered onto recommend/compare):

| Property | What to assert |
|---|---|
| Grounding | price/stock/promo/spec/link only from payload; disclose missing |
| Anti-hallucination | never invent SKU, price, spec, brand, link, promo |
| Clarify-vs-answer | ask only when it changes the result; else proceed; <=1 question |
| Tool selection | recommend->search, compare->compare-search, text when no tool fits |
| Tool discipline | one tool/turn; no invented tool; no same-tool-twice-in-a-row |
| Refuse-on-uncertainty | insufficient/unverifiable context -> "need more info" |
| Conflict handling | conflicting context stated, not silently resolved |
| Guardrails | no code/API/system-prompt disclosure; hate refusal; no over-promise |
| Language mirroring | reply in the customer's language/register |
| Robustness | no-diacritics, typos, terse "1"/"ok"/"ya", inline PII, HTML "<br>", code-switch |
| Multi-turn state | carry need/budget/brand across turns; correction precedence |
| Grounded citations | product links only from payload/web_url, never fabricated |

## 6. Diverse product fixture (from `Spec_cate_gia.xlsx`)

Extract per-category product payloads from the xlsx (14 category sheets) into the
real tool-payload shape (`productcode`/`product_id`/`Trạng thái`/`Giá gốc`/
`Giá khuyến mãi`/`Khuyến mãi`/`Thông tin sản phẩm`/`Màu sắc`/`bảo hành`). Sample a
bounded, reviewable set per category (~15-30 products) seeded to include foils
for recommendation/comparison: cheap vs premium, in-stock vs out-of-stock,
missing-spec, promo vs no-promo, multiple brands, multiple variants. Pin a
`catalog_snapshot` version. The existing aircon fixture can be the Máy lạnh slice.

## 7. Per-turn case schema

```
conversation_id, turn_index, category, capability,   # recommend | compare | support
input { message, user_info?, prior_state? },
expected {
  intent,
  tool_call { name, key_args } | null,      # exactly one, or null (text)
  slots_extracted {},                        # budget, use_case, brand, spec, qty, color, models[]
  candidate_filter {},                       # budget cap, spec threshold, stock, region
  grounded_claims [],                        # price/stock/promo/spec/link -> payload path
  answer_type,                               # recommendation | comparison | clarification | no_match | guardrail_block | text
  next_action
},
assertions [], judge_rubric_id, severity_if_failed, risk_level, coverage_axes []
```

## 8. Conversation journeys (compare/recommend-centric, diverse categories)

Each journey = a full multi-turn advisory thread; recommend+compare are the core
turns, funnel turns are short tails. Mirror the real logs (anonymized):

- J1 Desktop+monitor gaming (budget+use-case recommend -> spec Q&A -> add
  monitor -> compatibility -> compare 2 monitors -> pick).
- J2 Fridge comparison (compare two by model code -> which fits -> recommend).
- J3 Phone for student (vague budget 2.59M recommend -> variant color/RAM ->
  compare two candidates -> accessory).
- J4 Aircon by room/HP (recommend by capacity+budget -> compare 2 models ->
  install/delivery tail).
- J5 Washing machine by capacity (recommend 12kg Casper -> compare vs alt ->
  Sunday-delivery tail).
- J6 Tablet (recommend -> compare OPPO vs alt -> case accessory -> branch stock).
- J7 Monitor by spec (recommend 24" ~3.99M -> compare IPS vs VA -> pick).
- J8 TV / large category (recommend by size+budget -> compare 2 -> promo).
- J9 Cross-category / ambiguous ("máy tính" -> clarify desktop vs laptop ->
  recommend -> compare).

## 9. Scale & distribution

- ~9 journeys x ~8-12 turns, recommend/compare-weighted, + ~30-40 atomic edge &
  property cases = ~120-150 scored cases.
- >=60% of cases are recommend or compare. Every recommendation edge (3d) and
  comparison edge (4c) gets >=1 case; each P0 property (grounding, tool
  selection, anti-hallucination, no_match) gets >=2.
- Diverse categories: >=8 categories represented across journeys + atomics.

## 10. Verification (anti-plausibility)

Per turn: expected tool+args derivable from state+user_info; every grounded_claim
traces to a payload field; recommendation candidate_filter reproducible by hand
from the fixture; comparison values reproducible from both payloads; guardrail
cases checked against system-prompt rules; no asserted price/stock/promo without
a source; no real PII anywhere (use synthetic placeholders).

## 11. Governance / housekeeping

- `data/` is gitignored (`.gitignore:57`); new golden files need `git add -f`
  or a `.gitignore` exception.
- Generating files (fixture extraction + JSONL authoring) is change work; run
  harness intake + a registered story first.
- Never copy real PII from the source logs into any golden artifact.
- Supersedes the earlier aircon-only plan at
  `data/aircon-m1-test-data/aircon-m1-golden-dataset-expansion-plan.md`.
