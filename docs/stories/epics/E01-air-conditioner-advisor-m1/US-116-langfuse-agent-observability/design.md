# US-116 — Langfuse Agent Observability Design

## Goal

Instrument the implemented M1 decision boundaries that provide the most value
for bug diagnosis and model improvement without changing behavior or contracts.

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

1. US-207 provides the shared adapter and `advisor_turn` lifecycle.
2. `input_guard_node`, `classify_and_extract`, and `merge_state` create the
   canonical `input_guardrail`, `intent_classifier`, and `state_merge`
   observations when an active turn context exists.
3. Intent/extraction provider calls create nested generation observations with
   full prompt/output and resolved route metadata.
4. Direct node calls without active tracing use the no-op adapter and preserve
   existing tests and behavior.
5. Later M1 stories add only high-value observations justified by debugging or
   model-improvement needs; unimplemented nodes never produce placeholder spans.

## Priority Observation Tree

```text
advisor_turn
├── input_guardrail
├── intent_classifier
│   ├── intent_model_call (generation, one per candidate attempt)
│   └── deterministic_fallback (span, when used)
├── state_merge
└── future priority boundaries when implemented:
    ├── product_search
    ├── hard_constraint_filter
    ├── role_ranking
    ├── response_generation
    ├── output_validation
    └── memory_write
```

Current US-116 proof covers the three implemented M1 boundaries. The accepted
architecture's detailed canonical tree remains product authority, but this
story intentionally does not manufacture or instrument missing/low-value steps.

## Interface Contract

### Observation adapter

Consume `backend/app/observability/langfuse.py` created by US-207:

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

- Wrap `backend/app/graph/nodes/input_guard.py::input_guard_node`.
- Wrap `backend/app/graph/nodes/intent.py::classify_and_extract` and its
  provider/fallback path.
- Wrap `backend/app/graph/nodes/merge_state.py::merge_state`.
- Add tests for these three priority boundaries and their provider fallback.

M1 API response reconciliation remains owned by its future gateway story. This
story does not add an incomplete gateway merely to expose `trace_id`.

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

- Each selected M1 priority boundary records its exact observation name under
  an active `advisor_turn`.
- Intent/extraction candidate attempts record nested generations with
  role/provider/model and full raw input/output.
- Langfuse failures leave agent responses and deterministic fallback behavior
  unchanged, while recording degradation when possible.
- Disabled or missing configuration is a no-op.
- Focused tests prove current-node tree shape, raw payloads, error closure, and
  unchanged node outputs without requiring spans for every helper.
