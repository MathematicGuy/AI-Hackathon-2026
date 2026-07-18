# Design

## Domain Model

- **Release**: immutable source bundle identified by Git commit SHA.
- **Active release**: release directory selected by the server's `current`
  symlink.
- **Deployment run**: one GitHub Actions CD execution for one commit.
- **Health state**: pass/fail result from the deployed service health endpoint.

No product records or database migrations are introduced.

## Application Flow

1. CI runs `frontend` install, lint, typecheck, and build checks.
2. CD is restricted to a successful `push` on `main` and uses a concurrency
   group so only one production deploy is active.
3. The runner creates a bundle from the checked-out commit, excluding `.env*`,
   credentials, caches, and generated dependency folders.
4. SSH creates a timestamped release directory, uploads/extracts the bundle,
   and runs the root `docker-compose.yml` frontend service using the host-side
   `.env`.
5. The remote script waits for health, switches `current` only after success,
   and retains the prior release.
6. On failure it leaves `current` unchanged, emits bounded diagnostics, and
   exits non-zero. Rollback switches to the previous known-good release.

## Interface Contract

- `pull_request`: CI only.
- `push` to `main`: CI, then CD.
- Optional protected `workflow_dispatch`: redeploy a chosen commit only after
  the same checks.
- Required secrets: `DO_HOST`, `DO_USERNAME`, `DO_SSH_KEY`.
- Non-secret repository/environment variables may set deploy root, SSH port,
  health URL, and Compose path with safe defaults.
- Ubuntu 22.04+ must have Docker Engine, Compose plugin, a non-interactive
  deploy user, and a server-side `.env` outside the release bundle. The
  frontend container must expose its configured host port and answer its root
  health check.

No application API route or response contract changes.

## Data Model

No tables, indexes, migrations, or retention policies change. Release metadata
is filesystem state under the operator-owned deploy root with bounded cleanup.

## UI / Platform Impact

The platform boundary is a GitHub Linux runner to Ubuntu. Workflow steps use
pinned actions, shell strict mode, temporary SSH keys with mode 0600, and a
bounded remote command surface.

## Observability

GitHub summaries include commit SHA, release directory, health result, and
rollback status, never secret values. Remote failure diagnostics are limited to
`docker compose ps` and bounded service logs.

## Alternatives Considered

1. Remote `git pull` — rejected because it needs repository credentials and can
   drift from the CI-tested commit.
2. Container registry — deferred because it adds registry credentials and image
   lifecycle management.
3. Third-party SSH action — not selected by default; native OpenSSH keeps key
   handling and remote commands explicit.
