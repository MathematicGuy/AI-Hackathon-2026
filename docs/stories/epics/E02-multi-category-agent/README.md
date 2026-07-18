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
copy/edit/status/streaming UX (golden cases AGENT-G-013…021). Deferred:
policy retrieval over pgvector (the platform has no knowledge-base tables
yet); Langfuse judge wiring (keys not configured).
