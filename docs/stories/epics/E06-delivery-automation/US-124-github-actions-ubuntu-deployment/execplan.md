# Exec Plan

## Goal

Provide a reviewable, health-gated GitHub Actions pipeline that validates
`main` and deploys the exact validated revision to Ubuntu through SSH and
Docker Compose.

## Scope

In scope:

- Correct the existing frontend CI path/branch configuration.
- Add frontend CI and a dependent `main` CD workflow.
- Add release transfer, remote activation, health check, retention, rollback,
  and operator documentation.
- Add workflow/script validation and a staging deployment proof path.

Out of scope:

- Cloud provisioning, DNS/TLS/firewall automation, or managed database setup.
- Product feature/API changes or schema migrations.
- Registry, Kubernetes, or multi-host orchestration.

## Risk Classification

Risk flags:

- External systems: GitHub Actions, SSH, Docker, Ubuntu host.
- Audit/security: private key, host verification, secret handling.
- Cross-platform: GitHub runner and Ubuntu runtime.
- Existing behavior: current CI and Compose files change.
- Weak proof: no existing deploy/rollback harness.

Hard gates:

- Never log or transfer secret values.
- Fail closed on missing host-key verification, secrets, or health checks.
- Never activate an unhealthy release or deploy a non-`main` revision.
- Require human confirmation before the first production deployment.

## Work Phases

1. Discovery: confirm frontend deploy root, health endpoint, Compose service,
   and server `.env` ownership.
2. Design: accept the artifact-transfer and symlinked-release approach.
3. Validation planning: define local YAML/shell checks and disposable-host
   proof.
4. Implementation: update workflows, scripts, Compose/runtime docs, and tests.
5. Verification: run checks, build images, prove staging health failure and
   rollback, then run governance validation.
6. Harness update: attach fresh proof, trace, and completion evidence to US-124.

## Stop Conditions

Pause for human confirmation if production topology or `.env` is ambiguous,
privileged provisioning or destructive database changes appear, host-key
pinning cannot be established, or rollback cannot be demonstrated safely.
