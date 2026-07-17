# Design

## Domain Model

Pydantic v2 models freeze the M1 request envelope, intent output, customer
need, product/evidence records, role winners, cards, recommendation output, and
advisor state. Literal enums prevent unapproved intents, roles, and answer
types.

## Application Flow

This story defines no runtime handlers. It freezes graph node identifiers and
the canonical order that later LangGraph work must implement.

## Interface Contract

The API returns `session_id`, `request_id`, `trace_id`, and
`data: RecommendationOutput`. Model routing is fixed to GPT-5.4 Nano for
intent/extraction and `deepseek/deepseek-v4-flash` through OpenRouter for
grounded explanations.

## Data Model

No database or migration is introduced. Tests load the committed 14-product
catalog, 26 JSONL cases, validation manifest, ranking fixture, mock response,
and smoke scenarios.

## UI / Platform Impact

The mock response must be JSON-serializable and contain unique product cards
with role badges that match the deterministic winners.

## Observability

Node constants also freeze the canonical Langfuse span names. One user turn
maps to one `advisor_turn` trace.

## Alternatives Considered

1. Documentation-only freeze. Rejected because later code could drift without
   executable proof.
2. Implement runtime nodes now. Rejected because M1.1–M1.4 are gated on the
   contract freeze and have separate stories.

