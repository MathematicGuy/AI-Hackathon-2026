# Overview

## Current Behavior

No input guardrail exists. `INPUT_GUARD_ORDER` is declared in
`backend/app/graph/node_names.py` (word_count → regex_payload → nemo_input →
scope → intent_classifier), but no module implements it and no guardrail node
or tests exist. The frozen contract fixes the guardrail order and behavior; the
implementation is missing.

## Target Behavior

A deterministic, layered input guardrail runs before any customer-facing model:

- `evaluate_input(message, *, nemo) -> InputGuardResult` applies the stages in
  the exact frozen order and short-circuits at the first blocking stage.
- Word count ≥ 150 blocks (149 allowed) with the contract's Vietnamese block
  message; deterministic regex/payload rules reject empty input, repeated-char
  abuse, prompt-injection markers, unsupported encoded payloads, over-long URLs,
  unsafe-execution requests, and hidden-prompt/credential requests; an injected
  NeMo input rail runs next; the scope check keeps in-scope máy lạnh shopping and
  marks unrelated categories, auto-purchase, catalog modification, hidden-prompt,
  and code-execution as `unsupported`.
- NeMo unavailable degrades gracefully: continue only for deterministically
  low-risk in-scope shopping, otherwise fail closed; flag `guardrail_degraded`.
- A thin graph node applies the result over `WorkflowState`, writing
  `guardrail_flags` and a block marker.

## Affected Users

- End customers (safety and scope correctness before the LLM).
- USER1 lane owner (Lưu Thiện Việt Cường); US-101 integrators who wire the node.

## Affected Product Docs

- `docs/product/air-conditioner-advisor-m1-contract.md` — "Guardrail order".
- `docs/product/requirements/air-conditioner-advisor-m1-prd.md` §4.2, §10.2.
- `docs/product/architecture/air-conditioner-advisor-m1.md` §9.1, §12.

## Non-Goals

- Output guardrail (US-111/US-112) and intent extraction (US-103).
- Real NeMo Guardrails integration or any network call (injected rail only).
- Full gateway→state message wiring (US-101).
- Changing the frozen contract, enums, or `INPUT_GUARD_ORDER`.
