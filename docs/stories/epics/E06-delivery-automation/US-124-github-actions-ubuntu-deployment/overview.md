# US-124 GitHub Actions CI/CD to Ubuntu

## Current Behavior

- `.github/workflows/ci.yml` already targets the `frontend` directory, but its
  branch filters use `master` instead of the repository's `main` branch.
- `.github/workflows/backend-tests.yml` is a separate backend workflow and is
  outside this frontend-only story.
- No workflow deploys a verified frontend `main` revision to Ubuntu.

## Target Behavior

Every pull request and push to `main` runs the `frontend` checks. A push to
`main` deploys only after frontend CI succeeds. CD transfers the exact tested
frontend commit to Ubuntu over SSH, activates it with the root Docker Compose
frontend service, verifies health, and retains a previous release for rollback.

The workflow uses `DO_HOST`, `DO_USERNAME`, and `DO_SSH_KEY`. Host-key
verification, least-privilege commands, secret masking, and deploy concurrency
are mandatory.

## Affected Users

- Maintainers merging to `main`.
- Operators responsible for the Ubuntu host and its server-side `.env`.
- End users receiving the deployed release.

## Affected Product Docs

- `README.md`
- `docker-compose.production.yml` (was the root `docker-compose.yml`; revised
  by US-125 on 2026-07-19 when that stale template file was removed)
- `.github/workflows/`
- `docs/decisions/0017-github-actions-ubuntu-deployment.md`

## Non-Goals

- Provisioning a droplet, DNS, TLS, firewall, or managed database.
- Storing credentials in tracked files, artifacts, or logs.
- Replacing Docker Compose with Kubernetes or a registry.
- Changing backend APIs, advisor behavior, schemas, or catalog data.
