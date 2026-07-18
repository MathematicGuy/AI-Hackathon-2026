# Current Mission

## Demo promise

Vietnamese customers receive grounded, read-only product advice from the
available catalog data. The advisor does not invent product facts, grant
promotions, or modify operational data.

## Coordination scope

Đinh Nhật Thành owns cross-cutting coordination and architecture-document
maintenance for the current repository state. Detailed implementation status
and verification evidence belong in the Harness matrix and their owning
documentation, not in this tracker.

## Current documentation work

- Keep `ARCHITECTURE_v2.md` synchronized with the executable agent runtime.
- Keep this tracker limited to current coordination facts; do not duplicate
  work-item histories here.
- Keep `resources/` out of scope unless a human explicitly requests it.

## Current agent-runtime facts

- `backend/app/agent/` is a constrained single-agent pipeline, not a
  multi-agent mesh.
- The request path is FastAPI router -> process-local `AgentState` ->
  `run_turn` -> structured response.
- Guardrails run before understanding; deterministic code owns product search,
  filtering, suggestion, comparison, response validation, and fact fallback.
- Optional LLM capabilities are limited to understanding and text polishing.
- The agent currently loads a catalog snapshot through its adapter; it does not
  call the separate catalog API in its runtime path.
- Durable agent checkpoints and Langfuse tracing are target-state concerns, not
  wired features of the current agent path.

## Working boundaries

- `ARCHITECTURE_v2.md`
- `docs/team/now/THANH-NOW.md`

## Reference material

- `docs/product/air-conditioner-advisor-m1-contract.md`
- `docs/product/requirements/air-conditioner-advisor-m1-prd.md`
- `docs/product/architecture/air-conditioner-advisor-m1.md`
- `backend/app/agent/`
