# Validation

## Proof Strategy

The whole backend suite must pass before and after the change with no
previously passing test regressed, because the story touches shared agent
paths. Each new behavior gets its own deterministic unit coverage. The
comparison change additionally needs a live run against the running stack,
since a suite-green comparison payload does not prove the rendered table
matches the agent's own answer.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Comparison projection emits one row per dimension with real values on both sides; rows whose value is a placeholder are omitted; `winner_id` set only for rankable dimensions and left null on ties; `comparison` is null for non-comparison intents; oversized message rejected with 413; rate limit returns 429 after the configured burst; feedback logging records rating and session only, never message text; `REQUIRE_POSTGRES` true turns an adapter failure into a startup error; LLM client retries once on a transient error then falls through to the next candidate and logs both attempts. |
| Integration | `/api/v1/agent/respond` returns the comparison block for a two-product comparison turn and `null` otherwise; the streaming `done` event carries the identical object; existing agent contract tests still pass unchanged. |
| E2E | Live stack: a real comparison transcript renders a table whose rows and winner match the reply text; a stalled backend surfaces a timeout with a working retry instead of a permanent spinner. |
| Platform | Clean-host deploy drill: preflight creates the external volume, `docker compose -f docker-compose.production.yml up` reaches healthy, ingestion populates the catalog, and `/health` answers through nginx. |
| Performance | Not a target. Confirm only that the comparison projection adds no additional catalog scan beyond the existing one. |
| Logs/Audit | Backend emits no `print`; no customer message text appears in stdout for a feedback call; Postgres fallback or failure is logged with its cause. |

## Fixtures

- Existing deterministic catalog fixtures under `backend/tests`.
- Existing fake LLM transports; no network access required for the suite.
- For the comparison projection, two products from a category with registered
  dimensions (`36` máy lạnh) where at least one dimension differs and at least
  one is a placeholder on one side, to prove filtering.

## Commands

Baseline and regression:

```bash
python -m pytest backend/tests -q
cd frontend && npm run check
```

Focused during iteration:

```bash
python -m pytest backend/tests/unit/agent -q
```

Live E02 check against the running stack:

```bash
curl -s -X POST localhost:8080/api/v1/agent/respond \
  -H 'Content-Type: application/json' \
  -d '{"message":"so sánh 2 mẫu máy lạnh vừa rồi"}' | jq '.comparison'
```

## Acceptance Evidence

Baseline recorded 2026-07-19 before implementation:

- `python -m pytest backend/tests -q` — 410 passed, 17 skipped.
- `cd frontend && npm run check` — exit 0, production build succeeded.

After implementation, same day:

- `python -m pytest backend/tests -q` — **434 passed, 17 skipped**. No
  previously passing test regressed; the increase is 23 new tests in
  `backend/tests/unit/agent/test_production_hardening.py` plus one new
  contract case for the additive `comparison` field.
- `cd frontend && npm run check` — exit 0, lint, typecheck, and production
  build all clean. The duplicate-lockfile warning is gone with the removal of
  the empty root `package-lock.json`.
- `docker compose -f docker-compose.production.yml config` — valid.
- nginx config parses; the only error outside the compose network is
  `host not found in upstream "backend"`, which is service-name DNS and
  expected off-network.
- `bash scripts/deploy-preflight.sh` — correctly fails with exit 1 on a host
  with no `.env.production`, and reports the existing catalog volume.

### Live E02 run (2026-07-19)

Backend started on a spare port against the running catalog database with
`REQUIRE_POSTGRES=true`; the deployed stack was not disturbed.

Non-streaming `/api/v1/agent/respond`:

- Suggestion turn → `intent=new_search`, `comparison=null`.
- Comparison turn → `intent=compare_products`, payload with 2 products,
  `price_delta=700000`, and 4 dimension rows drawn from category 36 (máy lạnh):
  Phạm vi làm lạnh, Độ ồn, Inverter, Loại máy. `Độ ồn` winner is the 29 dB unit
  over the 33 dB unit, matching the `numeric_lower` rule.
- Oversized payload → **413**; 6th request inside the window → **429** with
  `Retry-After`; feedback → 200 and logs rating/session only.

Streaming `/api/v1/agent/respond/stream` (the path the frontend uses):

- The `done` event carries the identical comparison object; `null` on the
  non-comparison turn.
- Winner asserted against the streamed text: every `winner_id` appears in the
  reply as "… nhỉnh hơn" — the table cannot contradict the answer.
- Every row has a real value on both sides; placeholder specs are excluded.

### Deviation from plan

The clean-host deploy drill was not run: the host already has the stack and the
external catalog volume, and re-running the drill would have required tearing
down a running deployment. The preflight script was verified instead by running
it against a missing `.env.production` (exit 1) and confirming volume handling.
This remains open for the first real deploy host.

### Finding out of scope

The live persona check flagged "mình" in backend reply text (for example
"em nghĩ mình nên cân giữa mức chênh giá"). On inspection this is
customer-reference in the ordinary Vietnamese sales register, used consistently
across ~15 backend strings; the agent never self-addresses as
"mình/tôi/bạn" — self-reference is "em" everywhere. It is therefore not a
violation of the persona rule as written, and rewriting the register across
strings owned by other stories was left out of US-125. The frontend strings
that did address the customer as "mình"/"bạn" were corrected.
