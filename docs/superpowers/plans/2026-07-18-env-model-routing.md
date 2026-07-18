# Environment-Driven Model Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace code-owned model selections with a typed, fail-fast environment boundary and immutable role routing without changing public advisor data contracts.

**Architecture:** A private flat `BaseSettings` input model maps canonical environment variables, then constructs immutable nested public settings with secret-safe errors. A pure resolver converts the four configured roles into ordered immutable routes; bootstrap validation composes loading and routing before any future provider client is created.

**Tech Stack:** Python 3.12+, Pydantic 2.12+, pydantic-settings 2.12+, pytest 9

## Global Constraints

- All role, provider, base URL, and credential selections come from `.env` or process environment; none has a code default.
- Required missing or blank variables fail configuration construction and report variable names only.
- Intent classification and grounded explanation use `main`, then `fallback`.
- Need extraction uses `extraction`, then `fallback`.
- Judge uses `judge` only and fails closed.
- Required primary and fallback routes cannot resolve to the same provider/model pair.
- Model identifiers appear only in the operator-owned `.env`, never in Python, tests, plans, specs, ADRs, or story packets.
- Credentials use `SecretStr` and never appear in representations, validation errors, logs, traces, tests, or tracked files.
- Public advisor request, response, state, enum, and product contracts remain unchanged.
- Tests use isolated temporary dotenv files and never read the developer's real `.env`.

---

### Task 1: Typed settings loader and dotenv contract

**Files:**
- Modify: `pyproject.toml`
- Create: `.env.example`
- Create: `backend/app/config/__init__.py`
- Create: `backend/app/config/model_settings.py`
- Create: `backend/tests/unit/config/test_model_settings.py`

**Interfaces:**
- Produces: `ProviderName`, `ModelRoleSettings`, `ProviderConnectionSettings`, `ModelSettings`, `ModelConfigurationError`, and `load_model_settings(env_file: Path | None = None) -> ModelSettings`.
- Environment names: `MAIN_LLM_PROVIDER`, `MAIN_LLM_MODEL`, `EXTRACTION_LLM_PROVIDER`, `EXTRACTION_LLM_MODEL`, `FALLBACK_LLM_PROVIDER`, `FALLBACK_LLM_MODEL`, `JUDGE_LLM_PROVIDER`, `JUDGE_LLM_MODEL`, `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, `MISTRAL_API_KEY`, `MISTRAL_BASE_URL`, and optional `MODEL_ENV_FILE`.

- [ ] **Step 1: Add the typed settings dependency**

Add `"pydantic-settings>=2.12,<3",` beside the existing Pydantic dependency. Do not add a second dotenv library; pydantic-settings owns dotenv loading.

- [ ] **Step 2: Write RED settings tests**

Create a canonical `ENV_NAMES` tuple and a `complete_env()` helper whose model values are obvious non-production sentinels, URLs use reserved `.example` hosts, and credentials are test-only sentinel strings. Tests must cover:

```python
def test_loads_all_roles_and_connections_from_explicit_dotenv(tmp_path, monkeypatch): ...
def test_process_environment_overrides_dotenv(tmp_path, monkeypatch): ...
def test_model_env_file_selects_dotenv(tmp_path, monkeypatch): ...
@pytest.mark.parametrize("missing_name", ENV_NAMES)
def test_missing_required_variable_reports_name_only(...): ...
@pytest.mark.parametrize("blank_name", ENV_NAMES)
def test_blank_required_variable_reports_name_only(...): ...
@pytest.mark.parametrize("name, invalid_value", [("MAIN_LLM_PROVIDER", "unsupported"), ("MISTRAL_BASE_URL", "not-a-url")])
def test_invalid_values_are_sanitized(...): ...
def test_secret_values_are_redacted_from_repr(tmp_path, monkeypatch): ...
```

Every test must clear all canonical names plus `MODEL_ENV_FILE` from the process environment before loading. Assertions may compare against local sentinel fixture values, but must not use any production model identifier or credential.

- [ ] **Step 3: Run RED verification**

Run: `rtk pytest backend/tests/unit/config/test_model_settings.py -q`

Expected: FAIL during collection because `backend.app.config.model_settings` does not exist.

- [ ] **Step 4: Implement immutable nested settings**

Implement the public value objects with frozen Pydantic configuration and hidden validation inputs:

```python
from enum import StrEnum
from pathlib import Path
import os
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, SecretStr, StringConstraints, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

NonBlankString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ProviderName(StrEnum):
    OPENROUTER = "openrouter"
    MISTRAL = "mistral"


class _FrozenConfigModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)


class ModelRoleSettings(_FrozenConfigModel):
    provider: ProviderName
    model: NonBlankString


class ProviderConnectionSettings(_FrozenConfigModel):
    base_url: HttpUrl
    api_key: SecretStr


class ModelSettings(_FrozenConfigModel):
    main: ModelRoleSettings
    extraction: ModelRoleSettings
    fallback: ModelRoleSettings
    judge: ModelRoleSettings
    openrouter: ProviderConnectionSettings
    mistral: ProviderConnectionSettings

    def connection_for(self, provider: ProviderName) -> ProviderConnectionSettings:
        return self.openrouter if provider is ProviderName.OPENROUTER else self.mistral


class ModelConfigurationError(RuntimeError):
    """Secret-safe configuration failure containing environment names only."""
```

Use a private `_RawModelSettings(BaseSettings)` with one required field per canonical environment name and `Field(validation_alias="...")`. Set `extra="ignore"`, `case_sensitive=True`, `env_file_encoding="utf-8"`, `env_ignore_empty=False`, and `hide_input_in_errors=True`. Model fields use `NonBlankString`; credential fields use `SecretStr` plus a before-validator that rejects whitespace-only strings without returning or formatting the input.

`load_model_settings()` must:

1. use its explicit `env_file` argument when supplied;
2. otherwise use a non-blank process `MODEL_ENV_FILE` value;
3. otherwise use `Path.cwd() / ".env"`;
4. construct `_RawModelSettings(_env_file=selected_path)` so process variables override dotenv;
5. catch `ValidationError`, map every error location to its canonical environment alias, and raise `ModelConfigurationError("Invalid model configuration: " + ", ".join(names))` with no chained exception text;
6. return nested `ModelSettings` with all four roles and both connections.

The alias map is the single source for both `Field(validation_alias=...)` declarations and error-name sanitization. Do not include raw values in any exception.

- [ ] **Step 5: Add the tracked environment template**

Create `.env.example` with exactly the canonical required variable names and empty values, grouped into role selection and provider connectivity. Include optional `MODEL_ENV_FILE=` last. Do not include a model, provider, URL, or credential value.

- [ ] **Step 6: Run GREEN verification**

Run: `rtk pytest backend/tests/unit/config/test_model_settings.py -q`

Expected: all settings tests pass without reading the repository `.env`.

- [ ] **Step 7: Commit**

```powershell
rtk git add pyproject.toml .env.example backend/app/config backend/tests/unit/config/test_model_settings.py
rtk git commit -m "feat(models): add env-driven settings boundary"
```

---

### Task 2: Immutable role routing and bootstrap validation

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/routing.py`
- Modify: `backend/app/config/model_settings.py`
- Create: `backend/tests/unit/models/test_routing.py`

**Interfaces:**
- Consumes: `ModelSettings.connection_for(provider)` from Task 1.
- Produces: `ResolvedModelRoute`, `ModelRoutes`, `ModelRoutingError`, `resolve_model_routes(settings: ModelSettings) -> ModelRoutes`, and `validate_model_configuration(env_file: Path | None = None) -> None`.

- [ ] **Step 1: Write RED routing tests**

Build settings only through `load_model_settings()` and an isolated temporary dotenv helper. Cover:

```python
def test_intent_and_explanation_use_main_then_fallback(...): ...
def test_extraction_uses_extraction_then_fallback(...): ...
def test_judge_has_no_fallback(...): ...
def test_routes_and_route_sequences_are_immutable(...): ...
@pytest.mark.parametrize("primary", ["main", "extraction"])
def test_duplicate_primary_and_fallback_are_rejected(primary, ...): ...
def test_bootstrap_validation_constructs_settings_and_routes(...): ...
def test_bootstrap_validation_fails_on_duplicate_route(...): ...
def test_route_repr_does_not_expose_credentials(...): ...
```

Duplicate-route failures must mention only the role names, never provider, model, URL, or credential values.

- [ ] **Step 2: Run RED verification**

Run: `rtk pytest backend/tests/unit/models/test_routing.py -q`

Expected: FAIL during collection because `backend.app.models.routing` does not exist.

- [ ] **Step 3: Implement the pure immutable resolver**

Use frozen, slotted dataclasses and tuple route sequences:

```python
from dataclasses import dataclass, field

from pydantic import HttpUrl, SecretStr

from backend.app.config.model_settings import ModelRoleSettings, ModelSettings, ProviderName


@dataclass(frozen=True, slots=True)
class ResolvedModelRoute:
    provider: ProviderName
    model: str
    base_url: HttpUrl
    api_key: SecretStr = field(repr=False)


@dataclass(frozen=True, slots=True)
class ModelRoutes:
    intent: tuple[ResolvedModelRoute, ...]
    explanation: tuple[ResolvedModelRoute, ...]
    extraction: tuple[ResolvedModelRoute, ...]
    judge: tuple[ResolvedModelRoute, ...]


class ModelRoutingError(RuntimeError):
    """Invalid role routing that is safe to surface during bootstrap."""
```

`resolve_model_routes()` must reject equality of `(provider, model)` for main/fallback and extraction/fallback before constructing routes. Resolve each role through its configured provider connection. Return intent and explanation as the same ordered `(main, fallback)` tuple, extraction as `(extraction, fallback)`, and judge as the one-item `(judge,)` tuple. The resolver performs no I/O, provider call, exception recovery, or logging.

- [ ] **Step 4: Add the bootstrap gate**

Add this function to `backend/app/config/model_settings.py`, using a local import to keep the dependency direction explicit and avoid an import cycle:

```python
def validate_model_configuration(env_file: Path | None = None) -> None:
    from backend.app.models.routing import resolve_model_routes

    resolve_model_routes(load_model_settings(env_file))
```

Export only stable public names from the two package `__init__.py` files. Do not instantiate settings at import time.

- [ ] **Step 5: Run GREEN and integration verification**

Run: `rtk pytest backend/tests/unit/config/test_model_settings.py backend/tests/unit/models/test_routing.py -q`

Expected: all configuration and routing tests pass.

- [ ] **Step 6: Commit**

```powershell
rtk git add backend/app/config backend/app/models backend/tests/unit/models/test_routing.py
rtk git commit -m "feat(models): resolve immutable role routes"
```

---

### Task 3: Remove runtime model constants from public contracts

**Files:**
- Modify: `backend/app/contracts/schemas.py`
- Modify: `backend/app/contracts/__init__.py`
- Modify: `backend/tests/contract/test_m1_contracts.py`

**Interfaces:**
- Consumes: runtime model selection now belongs only to `backend.app.config` and `backend.app.models`.
- Preserves: every existing advisor request, response, state, enum, graph, product, and fixture assertion.

- [ ] **Step 1: Write the RED contract-separation assertion**

Remove imports of `INTENT_MODEL`, `EXPLANATION_PROVIDER`, and `EXPLANATION_MODEL`. Rename `test_frozen_enums_and_model_routing` to `test_frozen_enums_and_runtime_model_separation`, retain all enum assertions, then add:

```python
import backend.app.contracts as contracts
import backend.app.contracts.schemas as schemas


for name in ("INTENT_MODEL", "EXPLANATION_PROVIDER", "EXPLANATION_MODEL"):
    assert not hasattr(schemas, name)
    assert not hasattr(contracts, name)
```

- [ ] **Step 2: Run RED verification**

Run: `rtk pytest backend/tests/contract/test_m1_contracts.py -q`

Expected: FAIL because the legacy runtime constants remain exported.

- [ ] **Step 3: Remove only the runtime constants**

Delete the three assignments from `schemas.py`, remove their re-exports and `__all__` entries from `contracts/__init__.py`, and make no other public contract change.

- [ ] **Step 4: Run GREEN verification**

Run: `rtk pytest backend/tests/contract/test_m1_contracts.py backend/tests/unit/config/test_model_settings.py backend/tests/unit/models/test_routing.py -q`

Expected: all focused contract, configuration, and routing tests pass.

- [ ] **Step 5: Commit**

```powershell
rtk git add backend/app/contracts backend/tests/contract/test_m1_contracts.py
rtk git commit -m "refactor(contracts): separate runtime model routing"
```

---

### Task 4: Migrate local configuration and de-harden authoritative docs

**Files:**
- Modify locally, never stage: `.env`
- Modify: `docs/decisions/0009-m1-explanation-model-routing.md`
- Modify: `ARCHITECTURE.md`
- Modify: `WORKFLOW-MVP(4).md`
- Modify: `docs/product/air-conditioner-advisor-m1-contract.md`
- Modify: `docs/superpowers/plans/2026-07-17-m1-1-through-m1-8.md`
- Modify: `docs/stories/epics/E01-air-conditioner-advisor-m1/US-122-environment-model-routing/validation.md`

**Interfaces:**
- Consumes: the canonical environment names and role behavior from Tasks 1–3.
- Produces: operator-owned local values plus role-based architecture, workflow, ADR, product-contract, and active-plan text.

- [ ] **Step 1: Migrate the ignored local `.env` without exposing values**

Preserve `TEAM_MEMBER` and every unrelated variable. Replace legacy `DEFAULT_MODEL` with the canonical main role key, ensure the four role provider/model pairs and two provider base URL/API-key pairs are present, and remove duplicate legacy routing keys. Use the user-approved values already supplied for this repository. Do not print the file, values, or a dotenv diff; verify names only with a sanitized command. Never stage `.env`.

- [ ] **Step 2: Amend ADR 0009 with the role contract**

Replace literal provider/model decisions with these exact decisions:

- model identifiers and provider selections are operator-owned environment values;
- intent and grounded explanation share the main route;
- need extraction has its own extraction route;
- main and extraction failures use fallback;
- judge uses only the judge route and fails closed;
- changing a model identifier no longer requires a code, contract, plan, spec, or ADR edit, while changing role responsibilities or failure policy does.

- [ ] **Step 3: Update architecture and workflow references**

Replace runtime model-name/provider literals in customer-facing role diagrams, tables, prose, and trace examples with `main`, `extraction`, `fallback`, `judge`, or the corresponding environment variable name. Keep the engineering coding-assistant entry unchanged because it is not a customer runtime role. Update trace metadata examples to record role plus resolved provider/model metadata symbolically, not a concrete model identifier.

- [ ] **Step 4: Update the product contract and active implementation plan**

In `docs/product/air-conditioner-advisor-m1-contract.md`, replace the literal explainer selection with the environment-owned role policy. In Task 7 of the active M1 plan, replace `INTENT_MODEL` with injected `main`/`extraction` routes and state that intent classification uses main while need extraction uses extraction, with fallback on either provider failure. In the explanation tasks, refer to the configured main route and immutable fallback order. Do not change deterministic ranking or public data contracts.

- [ ] **Step 5: Verify no production model identifier remains in the changed routing surface**

Run a scoped literal scan across the ADR, architecture, workflow, product contract, active plan, approved routing spec, US-122 packet, Python source, and routing tests. Expected: no production model identifier; any match must be either the unchanged engineering-assistant entry explicitly allowed above or removed before commit. Also scan staged content for credential-like assignments and verify `.env` is absent from `rtk git status --short` and the staged file list.

- [ ] **Step 6: Run full backend verification and record evidence**

Run:

```powershell
rtk pytest backend/tests/unit/config/test_model_settings.py backend/tests/unit/models/test_routing.py backend/tests/contract -q
rtk pytest backend/tests -q
rtk git diff --check
```

Record exact pass counts and the scoped scan result in US-122 `validation.md`. If a third-party pytest plugin causes an environment-only failure, rerun with the repository's established `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` pattern and record both outcomes accurately.

- [ ] **Step 7: Commit tracked migration artifacts**

```powershell
rtk git add docs/decisions/0009-m1-explanation-model-routing.md ARCHITECTURE.md "WORKFLOW-MVP(4).md" docs/product/air-conditioner-advisor-m1-contract.md docs/superpowers/plans/2026-07-17-m1-1-through-m1-8.md docs/stories/epics/E01-air-conditioner-advisor-m1/US-122-environment-model-routing/validation.md
rtk git diff --cached --check
rtk git commit -m "docs(models): make runtime routing environment-owned"
```

---

## Completion Gates

- Run `rtk pytest backend/tests -q` and read the result.
- Run `rtk git diff --check` and read the result.
- Confirm `.env` contains every canonical name without displaying values and remains ignored/untracked.
- Confirm no public contract shape changed beyond removal of the three runtime constants.
- Record Harness unit, integration, platform, and trace proof for US-122; run `harness-cli audit` followed by `harness-cli propose`.
- Obtain a clean per-task review after every task and a broad whole-branch review before branch finishing.
