# Environment-Driven Model Routing Design

**Status:** Approved design, pending implementation plan

**Intake:** High-risk maintenance request, Harness intake 11, proposed story US-122

## Goal

Replace code-owned model and provider selections with one typed, fail-fast configuration boundary loaded from `.env`. Runtime code, tests, plans, specs, and contracts must refer to model roles and environment-variable names rather than embed provider model identifiers.

## Scope

This design covers:

- configuration for main, extraction, fallback, and judge roles;
- provider credentials and base URLs;
- deterministic route ordering for intent, explanation, extraction, and evaluation;
- startup/bootstrap validation;
- removal of model-selection constants from public contract schemas;
- contract, configuration, and routing tests;
- updates to the routing ADR and architecture documentation.

This design does not implement provider calls, prompts, ranking, recommendation generation, or the future FastAPI gateway. The repository does not yet contain an executable backend composition root, so this change defines a bootstrap function that future entrypoints must call before serving traffic. The gateway story must wire that bootstrap into process startup.

## Role Semantics

| Workload | Primary role | Failure route |
| --- | --- | --- |
| Intent classification | `main` | `fallback` |
| Grounded explanation | `main` | `fallback` |
| Need extraction | `extraction` | `fallback` |
| Model-based evaluation | `judge` | Fail closed; no fallback |

The model assigned to each role is environment-owned. Changing a model identifier does not require a Python, plan, spec, ADR, or test edit.

## Environment Contract

### Role selection

- `MAIN_LLM_PROVIDER`
- `MAIN_LLM_MODEL`
- `EXTRACTION_LLM_PROVIDER`
- `EXTRACTION_LLM_MODEL`
- `FALLBACK_LLM_PROVIDER`
- `FALLBACK_LLM_MODEL`
- `JUDGE_LLM_PROVIDER`
- `JUDGE_LLM_MODEL`

### Provider connectivity

- `OPENROUTER_API_KEY`
- `OPENROUTER_BASE_URL`
- `MISTRAL_API_KEY`
- `MISTRAL_BASE_URL`

### Optional environment-file location

- `MODEL_ENV_FILE`

`MODEL_ENV_FILE` selects an explicit dotenv file for tests or deployment. When it is absent, the loader reads `.env` from the process working directory. Process environment values override dotenv values.

No listed variable has a model, provider, URL, or credential default in code. Missing or blank required variables fail configuration construction. Error messages list variable names only and never include values.

The existing legacy `DEFAULT_MODEL` key is not a runtime source after migration. The implementation updates the local ignored `.env` to the canonical role keys and adds a tracked `.env.example` containing variable names with non-secret empty values. Model identifiers remain only in the operator-owned `.env`.

## Configuration Boundary

Create `backend/app/config/model_settings.py` using `pydantic-settings`.

The module defines:

- `ProviderName`: the supported adapter identifiers;
- `ModelRoleSettings`: provider plus model name;
- `ProviderConnectionSettings`: base URL plus secret credential;
- `ModelSettings`: all four role settings and both provider connections;
- `load_model_settings(env_file: Path | None = None) -> ModelSettings`;
- `validate_model_configuration(env_file: Path | None = None) -> None`.

Credentials use `SecretStr`. Configuration objects must not expose secrets through `repr`, validation errors, logs, or trace metadata.

Loading is explicit rather than a side effect of importing contract modules. Tests can pass an isolated dotenv path or override process variables without reloading unrelated modules.

## Routing Boundary

Create `backend/app/models/routing.py` with a pure resolver that consumes `ModelSettings` and returns ordered immutable routes:

- intent and explanation: main, then fallback;
- extraction: extraction, then fallback;
- judge: judge only.

The resolver never calls a provider and never catches provider exceptions. Provider adapters consume its route order later. This keeps the current change independently testable while preserving the required failure policy for future runtime integration.

The resolver rejects configurations where a required primary role and its fallback resolve to the same provider/model pair. The judge may share a provider or model with extraction because its route and failure policy remain separate.

## Contract Separation

Remove `INTENT_MODEL`, `EXPLANATION_PROVIDER`, and `EXPLANATION_MODEL` from `backend/app/contracts/schemas.py` and `backend/app/contracts/__init__.py`.

Public request, response, state, enum, and product contracts remain unchanged. Runtime configuration is not part of the customer-facing schema surface.

Update contract tests to assert that model selections are absent from contract modules. Configuration tests own environment loading and routing assertions.

## Startup and Failure Behavior

`validate_model_configuration()` is the required application-bootstrap gate. It constructs settings and routing before any provider client, graph, or HTTP server is created.

Failure rules:

- missing or blank variable: startup/bootstrap fails with the missing variable name;
- invalid provider identifier: startup/bootstrap fails before client construction;
- invalid base URL: startup/bootstrap fails validation;
- duplicate primary/fallback route: startup/bootstrap fails validation;
- main or extraction provider failure at runtime: the future adapter tries the configured fallback and marks degraded execution;
- judge provider failure: evaluation fails closed and produces no substituted score.

Because no executable backend entrypoint exists today, US-122 proves the bootstrap gate directly. The gateway implementation must call it during application lifespan before accepting requests.

## Documentation Rules

Plans, specs, ADRs, story packets, test names, and comments describe roles and environment-variable names. They do not repeat model identifiers from `.env`.

Operational evidence may report the role and provider used. It must not record API keys, authorization headers, or raw dotenv content.

ADR `0009-m1-explanation-model-routing.md` must be amended to replace literal routing constants with this environment-owned role contract and to record that intent and explanation share the main route, extraction uses its own route, fallback serves main and extraction failures, and judge fails closed.

## Verification

Configuration tests use temporary dotenv files with sentinel values rather than production model identifiers or credentials.

Required proof:

- every required variable loads from dotenv;
- process environment overrides dotenv;
- missing and blank variables fail with names but not values;
- secret fields are redacted in representations and errors;
- intent and explanation resolve to main then fallback;
- extraction resolves to extraction then fallback;
- judge resolves to judge only;
- duplicate primary/fallback routes fail;
- contract modules export no model-selection constants;
- the focused backend test suite passes without reading the developer's real `.env`.

No live provider call is required for this configuration-foundation story.

## Migration and Compatibility

1. Add the typed settings dependency and modules.
2. Add tests using isolated temporary environment data.
3. Remove model constants and update their contract tests.
4. Update the ignored local `.env` to canonical role/provider keys without printing or logging credential values.
5. Add `.env.example` with names only.
6. Amend ADR 0009, architecture routing text, and the active implementation plan to reference roles and environment keys.
7. Record US-122 proof and a high-risk trace.

The change is intentionally incompatible with clean environments that omit required model routing. That incompatibility is the approved fail-fast behavior.

## Acceptance Criteria

- No model identifier is hardcoded in Python source, tests, plans, specs, ADRs, or story packets within the changed routing surface.
- All role, provider, URL, and credential selections are loaded from `.env` or process environment.
- Missing configuration fails before runtime composition.
- Intent and explanation use the main route; extraction uses its separate route.
- Main and extraction failures resolve to the fallback route; judge has no fallback.
- Public advisor data contracts remain unchanged.
- Tests are isolated from the real `.env` and verify redaction and route order.
