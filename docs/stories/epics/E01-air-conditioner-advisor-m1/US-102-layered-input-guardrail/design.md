# Design

## Precision Principle (guardrail must not overfire)

The guardrail is tuned for **high precision on blocks**: it must never overfire
on a legitimate máy lạnh shopping request, while still keeping unrelated
categories and unsafe actions out of the recommendation flow. Concretely:

- Safety markers (injection, encoded payload, unsafe execution, credential /
  hidden-prompt) are tight, literal phrases a normal Vietnamese shopper never
  types; the repeated-character rule needs a 20-character run.
- The scope stage blocks another category only when there is **no** máy lạnh /
  điều hòa signal. A legitimate request that merely references another appliance
  ("phòng khách có tủ lạnh rồi, tôi cần mua máy lạnh") passes.
- Unsafe or automated actions (auto-purchase, catalog modification) always block
  regardless of category signal.
- Genuinely unrelated chit-chat is left to the intent classifier (US-103) to
  mark `unsupported` and answer with a scope-safe response, except in
  NeMo-degraded mode, where the scope stage fails closed for anything not
  clearly in-scope.

## Domain Model

- `InputGuardResult` (internal frozen dataclass, not in the public contract):
  `blocked: bool`, `stage: str | None` (the blocking stage name, one of
  `INPUT_GUARD_ORDER`), `answer_type: str | None` (`"guardrail_block"` when
  blocked), `flags: tuple[str, ...]` (e.g. `guardrail_degraded`), and
  `message: str | None` (the customer-facing block message). Passing input
  returns `blocked=False, stage=None`.
- `NemoInputRail` Protocol: `check(message) -> NemoVerdict` where `NemoVerdict`
  carries `allowed: bool` and `available: bool`. A default deterministic
  pass-through rail reports `available=False` so the fallback path is exercised
  without a real NeMo dependency.

## Application Flow

`evaluate_input(message, *, nemo)` applies stages in `INPUT_GUARD_ORDER` and
returns at the first block:

1. `word_count`: split on whitespace; `>= 150` → block with the contract's
   150-word Vietnamese message.
2. `regex_payload`: empty/whitespace-only, repeated-character abuse,
   prompt-injection markers, unsupported encoded payloads, over-long URLs,
   unsafe-execution requests, hidden-prompt/credential requests → block.
3. `nemo_input`: call the injected rail. If `available` and not `allowed` →
   block. If unavailable → do not block here; record `guardrail_degraded` and
   let the scope stage decide (fail closed for anything not clearly low-risk
   in-scope shopping).
4. `scope`: in-scope máy lạnh shopping (buy/recommend/compare/more/change/detail/
   availability) passes; unrelated categories, auto-purchase, catalog
   modification, hidden-prompt, and code-execution → block as `unsupported`.

`input_guard_node(state: WorkflowState) -> WorkflowState` reads the latest user
message (tolerant: `str` or mapping with `content`), runs `evaluate_input` with
the state-provided or default rail, appends result flags to `guardrail_flags`,
and on block sets a marker the router (US-101) turns into a `guardrail_block`
response. Pure apart from the injected rail; no I/O of its own.

## Interface Contract

- Inputs are plain strings and the injected `NemoInputRail`; outputs are the
  internal `InputGuardResult` / updated `WorkflowState`. No public API surface,
  no frozen-contract type changes. Order is asserted against
  `backend/app/graph/node_names.py` `INPUT_GUARD_ORDER`.

## Data Model

None. No persistence, schema, or migration.

## UI / Platform Impact

None.

## Observability

The `input_guardrail` span is emitted by the workflow integration story
(US-101/US-116). `evaluate_input` stays pure so that span is trivial to wrap;
this story only records `guardrail_flags`.

## Alternatives Considered

1. Bundle input and output guardrails together — rejected: output guardrail is
   US-111/US-112 with different dependencies and risk.
2. Depend on real NeMo Guardrails now — rejected: M1 uses an injected rail;
   real integration is deferred and must fail closed when unavailable.
3. A single regex mega-rule — rejected: the frozen order requires distinct,
   independently testable, short-circuiting stages.
