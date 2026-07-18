# US-207 — E02 Langfuse Agent Observability Design

## Architecture

Use an explicit fail-open adapter in `backend/app/observability/langfuse.py`.
Business code depends on a small observer protocol; only the adapter imports
Langfuse 3.15.0. A context-local stack links nested spans across async calls.
No-op handles preserve direct unit tests and unconfigured local execution.

## Priority Trace Tree

```text
agent_turn
├── input_guardrail
├── understanding
│   ├── understanding_model_call (generation, per candidate)
│   └── understanding_fallback (when used)
├── state_update
├── route_decision
├── policy_retrieval (policy path)
├── product_search (product path)
├── filter_and_rank (product path)
├── response_generation
│   └── response_polish_model_call (generation, when enabled)
├── output_validation
└── final_state
```

Only executed branches appear. Guardrail subtype, selected route, requested and
skipped roles, comparison/availability/no-match outcomes, clarification, polish
acceptance, and memory changes are metadata on these priority observations.
Observation names describe actual E02 behavior; M1 names remain separate under
US-116.

## API and Correlation

The route allocates `session_id`, `request_id`, and a 32-hex `trace_id` before
calling `run_turn`. `AgentResponse` adds `trace_id` for UI/log correlation.
`session_id` groups multi-turn conversations in Langfuse. Root tags include
`e02-agent` and the resolved environment.

## Payload and Metadata

- Root input/output: full request message, initial/final state snapshot, full
  response text, flags, intent, and presented IDs.
- Generation input/output: system prompt, user prompt, raw model output,
  candidate index, role, provider, model, temperature, error, and fallback use.
- Deterministic observations: search/filter/ranking inputs and summarized
  outputs, category, counts, product IDs, skipped roles, validation results,
  route/fallback reason, and before/after state changes.
- Excluded everywhere: API keys, authorization headers, secret environment
  values, and transport credentials.

## Failure Policy

- Use no-op observer when Langfuse credentials are missing or tracing disabled.
- Catch initialization/start/update/end/serialization/flush failures.
- Mark `observability_degraded` when possible; never replace business errors or
  existing deterministic fallbacks.
- Attempt one flush per HTTP request and one flush before demo CLI exit.
- No sampling for agent turns.

## SDK Policy

Use locked Langfuse Python SDK `3.15.0`. Major v4 upgrade is out of scope
because `pyproject.toml` intentionally caps `langfuse>=3,<4`; mixing migration
with instrumentation would expand risk and invalidate current lock proof.

## Alternatives Considered

1. Explicit observation boundaries — selected for stable product semantics,
   deterministic tests, and secret control.
2. Automatic decorators — rejected because helper-level noise and unstable
   names hide actual agent decisions.
3. OpenAI drop-in integration only — rejected as sole mechanism because it
   captures model calls but misses deterministic guardrail, memory, policy,
   search, ranking, validation, and fallback operations.

## Acceptance Criteria

- Every E02 branch records the priority decision boundaries it executes.
- Every extractor/polisher candidate attempt is a generation with full raw I/O
  and provider/model metadata.
- Root trace and API response share `trace_id`; turns share `session_id`.
- Trace failures do not alter response/status/body or fallback behavior.
- Tests prove normal, policy, compare, availability, no-match, stop, guardrail,
  deterministic fallback, polish accepted/rejected, and SDK failure paths
  without requiring a span for every helper call.
