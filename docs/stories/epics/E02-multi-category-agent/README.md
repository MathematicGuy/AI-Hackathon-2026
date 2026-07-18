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
