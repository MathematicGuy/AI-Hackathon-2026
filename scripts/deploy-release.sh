#!/usr/bin/env bash
# Remote activation for one CD release. Runs ON the Ubuntu host, invoked by
# .github/workflows/cd.yml over SSH. Never run it by hand mid-deploy.
#
#   bash deploy-release.sh <bundle.tar.gz> <sha>
#
# Contract with the workflow:
#   - the bundle is the exact tree of the commit CI validated, minus .env*
#   - .env.production lives on the host at ${DEPLOY_ROOT}/.env.production and
#     is symlinked into each release; it is never transferred
#   - the external pgdata volume already exists (scripts/deploy-preflight.sh)
#
# Honest limitation: docker-compose.production.yml pins the project name
# (`advisor-production`), so `up` reconciles the SAME stack no matter which
# release directory it runs from. There is no side-by-side blue/green. A bad
# release therefore replaces the running one and is rolled back by re-upping
# the previous release — expect seconds of downtime on a failed deploy, not
# zero. Trading that for real blue/green means per-release project names and a
# proxy switch, which is a larger change than US-124 scopes.

set -euo pipefail

BUNDLE="${1:?usage: deploy-release.sh <bundle.tar.gz> <sha>}"
SHA="${2:?usage: deploy-release.sh <bundle.tar.gz> <sha>}"

DEPLOY_ROOT="${DEPLOY_ROOT:-/opt/advisor}"
COMPOSE_FILE="docker-compose.production.yml"
HTTP_PORT="${HTTP_PORT:-8080}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:${HTTP_PORT}/health}"
HEALTH_RETRIES="${HEALTH_RETRIES:-30}"
HEALTH_INTERVAL="${HEALTH_INTERVAL:-5}"
KEEP_RELEASES="${KEEP_RELEASES:-5}"

RELEASES="${DEPLOY_ROOT}/releases"
CURRENT="${DEPLOY_ROOT}/current"
ENV_FILE="${DEPLOY_ROOT}/.env.production"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RELEASE="${RELEASES}/${STAMP}-${SHA:0:12}"

log() { echo "[deploy] $*"; }

# Resolve the release that is live right now, so a failed activation has
# something concrete to go back to. Empty on the very first deploy.
PREVIOUS=""
if [[ -L "${CURRENT}" ]]; then
    PREVIOUS="$(readlink -f "${CURRENT}")"
fi

compose_up() {
    # --build: images are built on the host. The bundle carries source, not
    # images, so the deployed artifact is source-exact rather than
    # byte-identical to anything CI produced.
    docker compose -f "${COMPOSE_FILE}" up -d --build --remove-orphans
}

health_ok() {
    local attempt=1
    while (( attempt <= HEALTH_RETRIES )); do
        if curl -fsS --max-time 5 "${HEALTH_URL}" >/dev/null 2>&1; then
            log "health passed on attempt ${attempt}"
            return 0
        fi
        sleep "${HEALTH_INTERVAL}"
        attempt=$(( attempt + 1 ))
    done
    return 1
}

# --- preconditions ----------------------------------------------------------
[[ -f "${ENV_FILE}" ]] || {
    echo "[deploy] FAIL ${ENV_FILE} is missing; provision it on the host first" >&2
    exit 1
}

mkdir -p "${RELEASES}"

# --- unpack -----------------------------------------------------------------
log "unpacking ${SHA:0:12} into ${RELEASE}"
mkdir -p "${RELEASE}"
tar -xzf "${BUNDLE}" -C "${RELEASE}"
rm -f "${BUNDLE}"

# The env file stays host-owned and outside the bundle; each release only
# borrows it. A symlink keeps one source of truth across releases.
ln -sfn "${ENV_FILE}" "${RELEASE}/.env.production"

# --- activate ---------------------------------------------------------------
cd "${RELEASE}"
log "starting stack from ${RELEASE}"
if ! compose_up; then
    log "FAIL compose up failed; leaving ${CURRENT} untouched"
    docker compose -f "${COMPOSE_FILE}" ps || true
    docker compose -f "${COMPOSE_FILE}" logs --tail 50 || true
    exit 1
fi

if health_ok; then
    # Atomic swap: write a new symlink beside the old one, then rename over it.
    # `ln -sfn` alone is not atomic when the target is an existing symlink.
    ln -sfn "${RELEASE}" "${CURRENT}.new"
    mv -Tf "${CURRENT}.new" "${CURRENT}"
    log "activated ${RELEASE}"
else
    log "FAIL health did not pass after $(( HEALTH_RETRIES * HEALTH_INTERVAL ))s"
    docker compose -f "${COMPOSE_FILE}" ps || true
    docker compose -f "${COMPOSE_FILE}" logs --tail 50 || true

    if [[ -n "${PREVIOUS}" && -d "${PREVIOUS}" ]]; then
        log "rolling back to ${PREVIOUS}"
        cd "${PREVIOUS}"
        compose_up || log "FAIL rollback compose up also failed; stack is down"
        if health_ok; then
            log "rollback healthy; ${CURRENT} still points at the prior release"
        else
            log "FAIL rollback did not become healthy; manual intervention needed"
        fi
    else
        log "no previous release to roll back to (first deploy)"
    fi
    exit 1
fi

# --- retention --------------------------------------------------------------
# Keep the active release plus a few behind it. Never touch the pgdata volume:
# it is external and lives outside every release directory by design.
cd "${RELEASES}"
mapfile -t stale < <(ls -1d ./*/ 2>/dev/null | sort -r | tail -n +$(( KEEP_RELEASES + 1 )))
for dir in "${stale[@]:-}"; do
    [[ -z "${dir}" ]] && continue
    candidate="$(readlink -f "${dir}")"
    [[ "${candidate}" == "$(readlink -f "${CURRENT}")" ]] && continue
    log "pruning ${candidate}"
    rm -rf "${candidate}"
done

log "done ${SHA:0:12}"
