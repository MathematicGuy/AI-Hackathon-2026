# E02 — Multi-Category Sales Agent

The product agent per ADR-0015/ADR-0016 and
`docs/product/architecture/multi-category-agent.md`: a Vietnamese, read-only,
proactive sales advisor over the 14 real categories in `data/dataset/`, with a
lazy policy engine (verbatim quoting, graceful degradation), per-category
cold-start scripts, fixed-format in-session preference memory, and grounded
salesman responses. Namespace `backend/app/agent/`; the M1 air-conditioner
pipeline stays untouched as the mock/evaluation rig.

| Story | Scope | Lane |
| --- | --- | --- |
| US-201 | Catalog foundation: Excel dataset adapter (swap-ready for the future DB), category registry, promotion parsing | normal |
| US-202 | Read-only product tools: search, aggregate, compare (promotion-forward), detail | normal |
| US-203 | Policy engine: corpus, retrieval, verbatim quoting, compliance degradation | high-risk |
| US-204 | Conversation: agent contracts, understand node, cold-start scenarios, preference memory | high-risk |
| US-205 | Proactive salesman prompts + sell node + deterministic grounding validation | normal |
| US-206 | Graph assembly, FastAPI endpoint, demo CLI, golden smoke scenarios | high-risk |

Dependency chain: US-201 → US-202 → (US-203, US-204) → US-205 → US-206.
Owner: Lưu Thiện Việt Cường (agent lane). Status/proof: Harness matrix.

Post-delivery rounds (all stories implemented, then re-completed with fresh
proof): the review round wired the real LLM extractor (tolerant env routes),
the also-consider section, pending-answer capture, the promotion-exploit
guard, and switch-cue protection; the atomic-layer audit round data-verified
every per-category performance attribute, reopened clarification cycles on
materially new searches, widened the suggestion pool, added unpriced
disclosure and the long-conversation memory suite. The data-platform round
added the Postgres adapter over Duy's `products` schema with Excel fallback,
per-category domain filter rules, optional LLM polish, and the golden eval
set. The live-test round (2026-07-19, from Cường's manual transcript) fixed
guardrail overfire (refusal now only on deliberate abuse; small talk gets a
friendly reply with a sales pivot), added four intents
(catalog_overview/price_range_query/promotion_inquiry/smalltalk) with
dedicated grounded flows, made policy answers natural (display names, no
filenames, literal-quote frame only on request, relevance floor), hid the
internal skip-role line, bundled the cold-start opener (2-3 questions),
introduced the +8% soft budget margin, added per-product/comparison
reasoning, and shipped the NDJSON streaming endpoint + frontend
copy/edit/status/streaming UX (golden cases AGENT-G-013…021). Live-test
round 2 (same day) made gpt-4o-mini the reasoning core (OPENAI_API_KEY
first, deepseek/Mistral fallbacks, full-context extractor prompt), made the
fallback state-aware (mid-flow follow-ups never dump the menu;
most_expensive role), added `question_clarification` (echoed questions get
an explained example, never policy), honest answers for uncarried products
(laptop/tivi/điện thoại + nearest alternatives), typo-tolerant money
parsing ("20-30 trịu"), fixed the asked-list reset that re-asked an
answered budget, added the suggestion debate line, hardened policy chunking
(generic-word stopwords, orphan-enum trim, no violation-apology on
validation failure), and shipped like/dislike + feedback endpoint,
replay-based edit, and consistent "em" self-address (golden AGENT-G-022…036).
The dimension round (round 3, same day) profiled every field of all 14
sheets and introduced the evidence-based dimension registry
(`catalog/dimensions.py`): suggestion roles are now preference-driven with
transparent evidence badges ("[Card mạnh nhất: 8 GB GDDR6]"), comparison and
the new `product_qa` intent answer deep follow-ups dimension-by-dimension
with thang-đo transparency, multi-part cold-start replies are captured in
full (monitor size ranges filter the pool), washer specs are live again
(stale "no spec columns" note retired), and all placeholder spec values are
filtered before any claim (golden AGENT-G-037…042; suite 186 with the
36-case baseline intact). Round 4 (2026-07-19) removed the short-message
limit at every layer (bare "ok"/"ừ" are exact-match agreements), made
comparison tool-driven ("So sánh 2 mẫu rẻ nhất/nổi bật" fetches its own
budget-aware pair), added explicit budget clear
(`AgentUnderstanding.clear_fields` — "không tra trong mức đó nữa" lifts the
window and re-opens the range question, old-reference numbers never
re-parsed), introduced JSON write-through session memory
(`AGENT_SESSION_DIR`, inspectable + restart-safe), and pinned a determinism
test (same scripted conversation twice → byte-identical replies); golden
AGENT-G-044…048, suite 228. The audit round (round 5, same day) probed the
whole pipeline and fixed five reproduced flaws with general fixes: money
bounds parse by context ("trên/hơn/tối thiểu X" is a floor — the old parser
read it as a ceiling; "từ X" had the same latent bug; compact "1tr5"/"X
triệu rưỡi" understood), cold-start capture is whitelisted to continuation
intents (interrupts are served without polluting memory and the question
stays pending), the detail tool is wired with a shared ordinal/name/
product_refs reference resolver (also powering "so sánh mẫu 1 với mẫu 3"),
explicit role locks release on new preferences, and clear_fields
generalized to brands/priorities/roles (golden AGENT-G-049…054, suite 258).
Round 6 (2026-07-19) deleted the template-era fake comparison card
(hardcoded products/ratings) from the frontend, widened the role-selection
pool to the whole candidate set ("máy lạnh đắt nhất" no longer picks the
20th-cheapest; a capping budget is disclosed), made auto-fetched comparison
copy honest, added policy topic-bigram doc bonuses ("tra cứu bảo hành" hits
the warranty doc, not the service price table) with crawl-heading trims,
gave product_qa an explicit outcome per dimension (verdict/tie/data gap)
with a pivot to a separating dimension, made "hả?" restate the last answer,
counted explicit role asks as narrowing facts, and unified the output
format (no arrows) — golden AGENT-G-055…059, suite 275. Deferred: policy
retrieval over pgvector (the platform has no knowledge-base tables yet);
Langfuse judge wiring (keys not configured).
