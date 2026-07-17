# Exec Plan

## Goal

Establish an environment-owned, fail-fast model-routing foundation before provider adapters and the FastAPI gateway are implemented.

## Scope

In scope:

- Typed dotenv/process-environment loading.
- Required role and provider validation.
- Immutable route ordering and duplicate-route rejection.
- Contract-module separation.
- Secret-safe errors and representations.
- Local `.env` migration without exposing values.
- Authoritative documentation and active-plan updates.

Out of scope:

- Live provider requests.
- Prompt implementation.
- Provider retry mechanics beyond route ordering.
- Gateway, graph, ranking, or frontend behavior.
- Unrelated environment or credential cleanup.

## Risk Classification

Risk flags:

- External systems.
- Public contracts.
- Existing behavior.

Hard gates:

- External provider routing.
- Accepted routing ADR amendment.

## Work Phases

1. Add RED settings-loader tests.
2. Implement typed settings and dotenv contract.
3. Add RED route-resolution tests.
4. Implement immutable route ordering and bootstrap validation.
5. Remove runtime model constants from public contracts.
6. Migrate local configuration and de-harden authoritative docs.
7. Run focused and full backend proof.
8. Record story proof, trace, audit, and proposals.

## Stop Conditions

Pause for human confirmation if:

- a live provider call becomes necessary;
- a credential would need to enter a tracked artifact or command output;
- public advisor request/response/state shapes would change;
- judge evaluation would require a fallback;
- validation requirements would need to be weakened;
- an executable gateway must be created early to claim startup behavior.
