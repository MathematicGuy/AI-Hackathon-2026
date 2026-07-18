# US-207 — E02 Langfuse Agent Observability

## Current Behavior

The live multi-category agent under `backend/app/agent/` serves
`POST /api/v1/agent/respond`. It runs promotion protection, layered input
guardrails, LLM understanding with deterministic fallback, preference memory,
policy/product routing, search/filter/ranking, grounded response generation,
optional LLM polish, validation, and presentation memory. None of those steps
currently emit Langfuse observations.

## Target Behavior

Every live agent request produces one `agent_turn` trace containing the
highest-value debugging and model-improvement observations. Full raw user/model
inputs and outputs are captured, while deterministic helpers are summarized at
decision boundaries instead of traced individually. Missing credentials and
SDK/export failures remain fail-open and never change customer-facing behavior.

## Affected Users

- Customers using the live multi-category agent.
- AI engineers debugging conversations, model fallback, grounding, and sales
  behavior.
- Operators filtering traces by session, route, category, intent, and outcome.

## Affected Product Docs

- `docs/product/architecture/multi-category-agent.md`
- `docs/decisions/0015-multi-category-agent-pivot.md`
- `docs/decisions/0016-policy-intent-and-compliance.md`
- `docs/TRACE_SPEC.md`

## Non-Goals

- Changing intent, memory, ranking, policy, grounding, or fallback behavior.
- Adding judge scores, datasets, prompt management, or dashboards.
- Instrumenting unrelated catalog API/database operations outside an agent turn.
