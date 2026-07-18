# Stories

Stories turn accepted product or governance intent into bounded implementation
and validation work. Active and completed packets live under `epics/`; future
candidates live in [`backlog.md`](backlog.md).

## Current Epics

- `E01-air-conditioner-advisor-m1`: Milestone 1 delivery stories and product
  contract. M1 is the air-conditioner (máy lạnh) slice of the general AI Product
  Comparison Advisor; the epic name reflects that category scope (ADR-001).
- `E04-ai-session-logging`: repository-native AI logging.
- `E05-repository-governance`: documentation authority and repository
  governance.

Query the active Harness matrix for current status rather than inferring status
from directory presence.

## Normal Story

Use [`../templates/story.md`](../templates/story.md) for normal feature work:

```text
docs/stories/epics/E01-domain-name/US-001-short-story-title.md
```

## High-Risk Story

Use [`../templates/high-risk-story/`](../templates/high-risk-story/) for
high-risk work:

```text
docs/stories/epics/E02-risky-domain/US-012-risky-story-title/
  overview.md
  design.md
  execplan.md
  validation.md
```

## Status Flow

```text
planned -> in_progress -> implemented
                  |
                  v
               changed
                  |
                  v
               retired
```

Story files define scope and evidence; the Harness durable layer is the
authoritative status and proof view.
