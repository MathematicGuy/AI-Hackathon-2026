# US-126 Exec Plan

## Goal

Promote the successful five-group pilot into a safe all-group collector,
versioned runtime mapping, additive Agent API projection, and disclosed
chatbot image.

## Scope

In scope:

- Explicit pilot and all-groups CLI modes with catalog-derived groups.
- Production JSON mapping, review CSV, checkpoint, resume, and force behavior.
- Runtime mapping validation, stable SKU assignment, and shared placeholder.
- Additive Agent API fields on JSON and stream responses.
- Chatbot image rendering with the “Hình ảnh minh họa” disclosure.
- Unit, contract, frontend build, and bounded live proof.

Out of scope:

- Product-level matching, external search providers, database writes, image
  downloads, and exact-SKU image claims.

## Risk Classification

Risk flags:

- External systems: public Điện Máy Xanh category-brand pages.
- Public contract: Agent JSON and NDJSON `done` event gain image fields.
- Existing behavior: text/comparison output and observability must remain
  unchanged.
- Multi-domain: collector, backend API, and frontend chatbot.
- Weak proof: the frontend has no component-test harness.

Hard gates:

- External provider behavior makes the story high-risk.

## Work Phases

1. Freeze the API/mapping decision and extend the story/file boundary.
2. Add catalog-derived group discovery and mutually exclusive safe CLI modes.
3. Add production mapping validation, checkpoint/resume/force tests, and a
   tracked mapping seeded from the reviewed pilot.
4. Add the API projection and contract tests without changing graph output.
5. Add disclosed frontend rendering and run lint/typecheck/build.
6. Run focused backend proof and a live pilot regression. Do not start the
   all-groups crawl unless `--all-groups` is explicitly invoked.
7. Record Harness proof and trace.

## Stop Conditions

Pause for human confirmation if:

- A group requires general web search or a non-DMX/TGDD source.
- The source page cannot distinguish the requested category and brand.
- A database or per-product write becomes necessary.
- Existing Agent text, comparison, or observability behavior regresses.
