# Design

## Domain Model

`ModelSettings` owns four model roles and provider connections. A model role contains a provider identifier and model identifier. A provider connection contains a validated base URL and secret credential. `ModelRoutes` is an immutable value object containing ordered routes for intent, explanation, extraction, and judge workloads.

Rules:

- intent and explanation resolve to main then fallback;
- extraction resolves to extraction then fallback;
- judge resolves only to judge;
- main/fallback and extraction/fallback pairs must differ;
- missing or blank settings are invalid;
- secrets are redacted from representations and errors.

## Application Flow

1. The composition boundary calls `validate_model_configuration()`.
2. The loader selects an explicit dotenv path, `MODEL_ENV_FILE`, or working-directory `.env`.
3. Process environment values override dotenv values.
4. Pydantic validates required role and provider fields.
5. The routing resolver builds ordered immutable routes and rejects duplicates.
6. Future provider adapters consume those routes through dependency injection.

No executable backend entrypoint exists yet. This story proves the bootstrap function directly; the gateway story must call it during application lifespan.

## Interface Contract

- `load_model_settings(env_file: Path | None = None) -> ModelSettings`
- `validate_model_configuration(env_file: Path | None = None) -> None`
- `resolve_model_routes(settings: ModelSettings) -> ModelRoutes`

Public advisor request, response, state, enum, and product contracts do not change. Runtime model constants are removed from the contracts package.

## Data Model

No database tables, migrations, indexes, or retained records are added. The local `.env` remains ignored. `.env.example` lists required variable names with empty non-secret values.

## UI / Platform Impact

No frontend or user-visible UI change. Python processes that compose model routing fail immediately when configuration is missing or invalid.

## Observability

Future traces may record role and provider identifiers. They must not record API keys, authorization headers, raw dotenv content, or rejected secret values. Judge failure produces no substituted score.

## Alternatives Considered

1. Direct `os.environ` reads at call sites. Rejected because configuration would be scattered and difficult to test.
2. A single JSON routing variable. Rejected because operational errors would be harder to validate and review.
3. Typed Pydantic Settings with role routing. Selected for centralized validation, redaction, and isolated tests.
