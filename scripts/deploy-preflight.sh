#!/usr/bin/env bash
# Preflight for docker-compose.production.yml.
#
#   bash scripts/deploy-preflight.sh
#
# Checks the two conditions that make a first deploy fail after everything
# looks healthy: the external pgdata volume does not exist yet, and the
# production environment file is missing or incomplete. Read-only except for
# creating the named volume, and safe to re-run.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${REPO_ROOT}/docker-compose.production.yml"
ENV_FILE="${REPO_ROOT}/.env.production"
ENV_EXAMPLE="${REPO_ROOT}/.env.production.example"
VOLUME_NAME="advisor-data-platform_pgdata"

# Values that must be non-empty for the stack to work in production. Provider
# keys are checked as a group further down: any one of them is enough.
REQUIRED_VARS=(POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD)
PROVIDER_VARS=(OPENAI_API_KEY OPENROUTER_API_KEY MISTRAL_API_KEY)

failures=0

fail() {
    echo "FAIL  $*" >&2
    failures=$((failures + 1))
}

ok() {
    echo "ok    $*"
}

echo "== deploy preflight =="

# --- tooling ----------------------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
    fail "docker is not installed or not on PATH"
else
    ok "docker present"
    if ! docker compose version >/dev/null 2>&1; then
        fail "the docker compose plugin is missing"
    else
        ok "docker compose plugin present"
    fi
fi

[[ -f "${COMPOSE_FILE}" ]] || fail "missing ${COMPOSE_FILE}"

# --- environment file -------------------------------------------------------
if [[ ! -f "${ENV_FILE}" ]]; then
    fail ".env.production is missing — copy ${ENV_EXAMPLE} and fill it in"
else
    ok ".env.production present"
    for var in "${REQUIRED_VARS[@]}"; do
        value="$(grep -E "^${var}=" "${ENV_FILE}" | tail -n1 | cut -d= -f2- || true)"
        if [[ -z "${value}" ]]; then
            fail "${var} is empty in .env.production"
        else
            # Never echo the value itself.
            ok "${var} is set"
        fi
    done

    provider_found=0
    for var in "${PROVIDER_VARS[@]}"; do
        value="$(grep -E "^${var}=" "${ENV_FILE}" | tail -n1 | cut -d= -f2- || true)"
        [[ -n "${value}" ]] && provider_found=1
    done
    if [[ "${provider_found}" -eq 0 ]]; then
        fail "no LLM provider key set — the agent cannot answer without one"
    else
        ok "at least one LLM provider key is set"
    fi

    # The developer .env must never be the production credential source.
    if [[ -f "${REPO_ROOT}/.env" ]] && cmp -s "${REPO_ROOT}/.env" "${ENV_FILE}"; then
        fail ".env.production is a copy of the developer .env — rotate and replace it"
    fi
fi

# --- external volume --------------------------------------------------------
# Declared external in the compose file, so `up` aborts if it does not exist.
if command -v docker >/dev/null 2>&1; then
    if docker volume inspect "${VOLUME_NAME}" >/dev/null 2>&1; then
        ok "volume ${VOLUME_NAME} exists"
    else
        echo "      creating missing volume ${VOLUME_NAME}"
        docker volume create "${VOLUME_NAME}" >/dev/null
        ok "volume ${VOLUME_NAME} created (catalog will be empty until ingestion runs)"
    fi
fi

echo
if [[ "${failures}" -gt 0 ]]; then
    echo "${failures} check(s) failed. Fix them before deploying." >&2
    exit 1
fi

cat <<'NEXT'
All checks passed. Deploy with:

  docker compose -f docker-compose.production.yml up -d --build

Then load the catalog once (otherwise the database is migrated but empty):

  docker compose -f docker-compose.production.yml run --rm ingestion

Verify:

  curl -fsS localhost:8080/health
NEXT
