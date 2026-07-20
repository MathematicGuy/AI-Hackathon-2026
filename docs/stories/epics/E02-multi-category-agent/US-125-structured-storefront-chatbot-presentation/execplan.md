# US-125 Exec Plan — Structured Storefront Chatbot Presentation

## Goal

Make `frontend/` render grounded, server-selected chatbot products and
comparisons with no hard-coded chatbot catalog data or client-side prose
classification.

## Scope

In scope:

- Additive E02 `AgentResponse.presentation` contract and mapper.
- Recommendation and comparison presentation built from verified tool results.
- Typed `frontend/` API boundary and message state.
- Data-driven comparison rendering and honest missing-data behavior.
- Backward-compatible text fallback, retry behavior, contract tests, E2E, and
  desktop/mobile visual proof.

Out of scope:

- `frontend-mvp/`, the M1 advisor endpoint, streaming, auth, durable sessions,
  database migrations, and new ranking or enrichment sources.

## Risk Classification

Risk flags:

- Public contracts.
- Existing behavior.
- Cross-platform desktop/mobile behavior.
- Weak proof around the current chatbot renderer.
- Multi-domain backend/frontend delivery.

Hard gates:

- None from auth, authorization, data loss, audit/security, or external provider
  behavior.

Lane: `high-risk` because five risk flags apply.

## Ownership Boundary

The `FRONTEND` lane may implement only:

- `frontend/src/components/ChatbotAssistant.tsx`
- `frontend/src/components/chat/ChatComparisonResult.tsx`
- `frontend/src/app/globals.css` when presentation layout requires it
- new typed client/types and targeted tests under `frontend/src/`
- this US-125 packet and `docs/team/now/FRONTEND-NOW.md`

Ngọc's explicit human direction on 2026-07-19 assigns only the E02
presentation-contract files named in `docs/team/now/FRONTEND-NOW.md` to this
lane on `deploy`. Cường retains all unnamed E02 files. Backend contract/tests
must land before frontend consumption.

## Work Phases

1. **Governance and contract.** Register US-125 and ADR-0017; align `deploy`,
   tracker scope, dependencies, and proof expectations; register the
   verification command before implementation.
2. **Backend contract tests first.** The E02 owner adds failing tests for the
   additive envelope, nullable product fields, stable SKU, recommendation data,
   comparison rows, first-turn clarification, session continuity, and fallback
   compatibility.
3. **Backend presentation mapping.** Preserve structured selection/comparison
   results through `AgentReply` and serialize them from the same grounded
   records as `text`. Do not re-query by `productidweb` in the browser.
4. **Frontend typed boundary.** Add the API client/parser, retain session and
   request metadata, store presentation in assistant messages, and make stale
   or invalid responses fall back to text/retry.
5. **Frontend renderer.** Remove `isComparisonQuery`, static products, static
   rows, and static follow-ups. Render the server discriminator and nullable
   fields; omit unsafe links and preserve the US-124 responsive interaction.
6. **Cross-stack proof.** Exercise clarification, recommendation, comparison,
   missing data, no-match/text-only behavior, policy response, error/retry, and
   multi-turn session flow against the shipped FastAPI app.
7. **Rollout and completion.** Deploy backend first, then frontend; run fresh
   proof, update Harness evidence, and complete the story only after all required
   validation passes.

## Stop Conditions

Pause before implementation if:

- Work requires an E02 backend file not explicitly listed in the FRONTEND tracker.
- Tracker, story, branch/worktree, or Harness state disagree.
- Implementation requires a breaking response change instead of ADR-0017's
  additive contract.
- A visual field would require fabricated data or an unapproved enrichment
  source.
- Validation requirements would need to be weakened.
