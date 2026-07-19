# Validation

## Proof Strategy

The story is complete only when workflow syntax, application checks, container
build, SSH transfer, health gating, and rollback behavior have fresh evidence.
A green CI workflow alone is insufficient without staging or disposable-host
deployment proof.

## Test Plan

| Layer | Cases |
| --- | --- |
| Unit | Release path sanitization; `.env` exclusion; rollback target selection. |
| Integration | CD is blocked by failed frontend CI; exact SHA is transferred; Compose receives only the server `.env`. |
| E2E | A `main` push deploys the tested frontend revision and passes health. |
| Platform | Ubuntu 22.04+ Docker/Compose, SSH host-key verification, key permissions, non-interactive Docker. |
| Performance | Bounded upload and health timeouts; no unbounded log streaming. |
| Logs/Audit | Job summaries and failure diagnostics contain SHA/status only. |

## Fixtures

- Disposable Ubuntu or staging host with Docker Compose.
- Non-production `.env` provisioned directly on that host.
- Dedicated deploy key installed for the deploy user.
- Pinned SSH host key and deterministic health endpoint.

## Commands

```text
TBD — add actionlint/shellcheck and backend/frontend commands when workflows exist.
```

## Acceptance Evidence

- [ ] CI passes on a pull request with the `frontend` checks.
- [ ] CD runs only for a successful `main` push and the exact tested SHA.
- [ ] Staging Compose deployment starts and health passes.
- [ ] Forced health failure leaves the prior release active and exits non-zero.
- [ ] Rollback restores the prior release without exposing secrets.
- [ ] README/operator docs and Harness trace are updated.
