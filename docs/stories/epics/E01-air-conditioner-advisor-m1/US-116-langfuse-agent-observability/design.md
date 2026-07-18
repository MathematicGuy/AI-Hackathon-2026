# US-116 — Langfuse Agent Observability Design

## Goal

Instrument the backend agent so every user turn is fully observable in
Langfuse without changing agent behavior or public API contracts.

## Domain Model

- **Advisor turn:** one user request and one agent response, represented by one
  root Langfuse observation named `advisor_turn`.
- **Observation:** a bounded product operation with stable name, parent, raw
  input/output, status, duration, and JSON metadata.
- **Provider generation:** one attempted extractor or polisher provider call,
  nested under its logical operation and identified by role, provider, and
  model.
- **Observation context:** an injected, optional dependency that carries the
  current root observation and shared trace metadata. It is a no-op when
  tracing is disabled or unavailable.

## Application Flow

1. The API allocates `session_id` and `request_id` before invoking `run_turn`.
2. The observation adapter starts one `advisor_turn` root observation and
   stores session/request/turn metadata.
3. `run_turn` wraps the existing canonical operations in stable child
   observations, including guardrail short-circuits, policy, compare,
   no-match, stop, fallback, and normal recommendation paths.
4. The extractor and polisher wrap every configured candidate attempt in a
   nested `generation` observation containing full system/user input and raw
   provider output. Existing candidate order and fallback behavior remain
   unchanged.
5. Each logical observation records deterministic inputs and outputs, product
   IDs/counts, state snapshots needed for evaluation, flags, and errors.
6. The root observation closes after response/error handling. The API performs
   one best-effort client flush; flush failures are non-fatal.

## Canonical Observation Tree

```text
advisor_turn
├── input_guardrail
├── intent_classifier
│   ├── intent_model_call (generation, one per candidate attempt)
│   └── deterministic_fallback (span, when used)
├── state_merge
├── intent_router
├── clarification_decision
├── product_search
├── product_normalization
├── hard_constraint_filter
├── availability_decision
├── best_overall_ranking
├── best_value_ranking
├── cheapest_qualified_ranking
├── ui_deduplication
├── response_generation
│   └── explanation_model_call (generation, one per candidate attempt)
├── output_validation
├── next_question_selection
└── memory_write
```

Conditional observations are still created when their path is reached. A
short-circuit records only observations that ran and marks the root outcome;
it must not invent observations for skipped work.

## Interface Contract

### Observation adapter

Create `backend/app/observability/langfuse.py` with a small protocol and
concrete implementations:

- `AgentObserver.start_turn(session_id, request_id, user_id, message, state) -> TurnObservation`
- `TurnObservation.span(name, input, metadata) -> ObservationHandle`
- `ObservationHandle.child(name, input, metadata, kind="span") -> ObservationHandle`
- `ObservationHandle.update(output, metadata, level, status_message)`
- `ObservationHandle.end()`
- `TurnObservation.finish(output, metadata, error=None)`
- `AgentObserver.flush()`

The adapter owns SDK calls, exception isolation, JSON normalization, and
environment-based enablement. Business modules depend only on the protocol.

### Injection points

- Add an optional observer/context field to `AgentDependencies`.
- Update the API route to create the request ID before `run_turn` and start the
  root turn observation.
- Update `run_turn` and `_product_flow` at existing operation boundaries.
- Update `LLMUnderstandingExtractor` and `LLMPolisher` around `_call` attempts.

No response DTO field changes are allowed. Existing `trace_id` behavior, when
present in the product contract, must remain compatible with the API envelope.

## Metadata and Payload Contract

Root metadata includes:

- `environment`, `session_id`, `request_id`, and `turn_number`;
- resolved role/provider/model names without credentials;
- prompt/rules/catalog versions;
- intent, guardrail status/flags, clarification count;
- retrieved, eligible, displayed, rejected, and shown product IDs/counts;
- final response status and `observability_degraded`.

Every logical observation stores full raw user/model inputs and outputs plus
deterministic intermediate inputs/outputs needed to reconstruct the turn.
Environment secrets, API keys, authorization headers, and transport credentials
are never stored in payloads or metadata.

## Failure Handling

- Missing Langfuse credentials or disabled tracing selects a no-op adapter.
- SDK initialization, observation creation/update/end, serialization, and flush
  failures are caught and recorded as bounded degradation state.
- Tracing failures never replace business exceptions, provider fallback, or
  deterministic response fallback.
- Business failures end observations with error level/status before existing
  exception or fallback behavior continues.
- No sampling is used for M1 agent turns; every request is attempted.

## Alternatives Considered

1. **Explicit observation boundaries (selected).** Stable product-level tree,
   predictable tests, and direct fail-open control; requires deliberate seams
   when new agent operations are added.
2. **Decorator tracing for every agent function.** Broad automatic coverage,
   but noisy unstable spans, harder secret control, and poor alignment with the
   frozen canonical tree.
3. **LangGraph callback-only tracing.** Central lifecycle handling when a
   compiled graph runs, but current imperative `run_turn` paths and direct
   provider calls would remain untraced without a second layer.

## Acceptance Criteria

- Normal recommendation creates one root `advisor_turn` and the complete
  canonical child tree.
- Guardrail, policy, compare, no-match, stop, fallback, and rejected-polish
  paths close all observations they start.
- Each extractor/polisher candidate attempt records a nested generation with
  role/provider/model and full raw input/output.
- Langfuse failures leave agent responses and deterministic fallback behavior
  unchanged, while recording degradation when possible.
- Disabled or missing configuration is a no-op.
- Focused tests prove tree shape, raw payloads, error closure, request/trace ID
  linkage, and non-fatal flush failure.
