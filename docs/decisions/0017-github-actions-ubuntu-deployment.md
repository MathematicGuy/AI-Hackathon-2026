# 0017 GitHub Actions Ubuntu Deployment

Date: 2026-07-18

## Status

Proposed

## Context

The repository has a frontend CI workflow targeting `frontend`, but its branch
filters use `master` while the repository deploy branch is `main`; no frontend
CD path exists.
The target is an Ubuntu server with `DO_HOST`, `DO_USERNAME`, and `DO_SSH_KEY`.
The design must avoid server-side repository credentials and prove that the
deployed revision passed CI.

## Decision

For US-124, use GitHub Actions to validate the checked-out `main` frontend
commit, transfer an immutable release bundle over native OpenSSH, and activate
it on Ubuntu with `docker-compose.production.yml`. Releases use timestamped
directories and an atomic `current` symlink. Health gates activation; the
previous release remains for rollback. Runtime environment values stay on the
server outside the bundle.

Amended by US-125 (2026-07-19): this decision originally named "the root Docker
Compose frontend service". That file was a leftover website-cloner template
with no backend and no database, and has been removed. The production stack is
`docker-compose.production.yml`, and its environment file is `.env.production`
— never the developer `.env`, whose credentials are treated as exposed.

## Alternatives Considered

1. Remote `git pull`, which needs repository credentials and can drift from the
   CI-tested commit.
2. Container registry publishing, which adds credentials and image lifecycle
   management not requested here.
3. Unpinned third-party SSH actions, which obscure key handling and remote
   command behavior.

## Consequences

Positive:

- The server receives the exact source revision validated by CI.
- Secrets remain in GitHub/host configuration and are excluded from artifacts.
- Atomic activation and retained releases make rollback explicit.

Tradeoffs:

- The operator must provision Docker, the deploy user, host-key pinning, and
  the server `.env.production` before the first deploy, and must run
  `scripts/deploy-preflight.sh` once to create the external `pgdata` volume.
- Artifact transfer is slower than pulling a prebuilt image and needs retention
  cleanup on the host.

## Follow-Up

- Confirm the frontend service name, deploy root, and health URL before implementation.
- Document deploy root, SSH port, health URL, and Compose path as non-secret
  configuration with safe defaults.
