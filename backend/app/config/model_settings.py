from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    SecretStr,
    StringConstraints,
    field_validator,
)
from pydantic_core import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProviderName(str, Enum):
    OPENROUTER = "openrouter"
    MISTRAL = "mistral"


NonBlankString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ModelRoleSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    provider: ProviderName
    model: NonBlankString


class ProviderConnectionSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    base_url: HttpUrl
    api_key: SecretStr


class ModelSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    main: ModelRoleSettings
    extraction: ModelRoleSettings
    fallback: ModelRoleSettings
    judge: ModelRoleSettings
    openrouter: ProviderConnectionSettings
    mistral: ProviderConnectionSettings

    def connection_for(self, provider: ProviderName) -> ProviderConnectionSettings:
        if provider is ProviderName.OPENROUTER:
            return self.openrouter
        if provider is ProviderName.MISTRAL:
            return self.mistral
        raise ValueError(f"Unsupported provider: {provider!r}")


class ModelConfigurationError(RuntimeError):
    """Raised when required model configuration is missing or invalid."""


class _RawModelSettings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        case_sensitive=True,
        env_file_encoding="utf-8",
        env_ignore_empty=False,
        hide_input_in_errors=True,
    )

    main_provider: ProviderName = Field(validation_alias="MAIN_LLM_PROVIDER")
    main_model: NonBlankString = Field(validation_alias="MAIN_LLM_MODEL")
    extraction_provider: ProviderName = Field(validation_alias="EXTRACTION_LLM_PROVIDER")
    extraction_model: NonBlankString = Field(validation_alias="EXTRACTION_LLM_MODEL")
    fallback_provider: ProviderName = Field(validation_alias="FALLBACK_LLM_PROVIDER")
    fallback_model: NonBlankString = Field(validation_alias="FALLBACK_LLM_MODEL")
    judge_provider: ProviderName = Field(validation_alias="JUDGE_LLM_PROVIDER")
    judge_model: NonBlankString = Field(validation_alias="JUDGE_LLM_MODEL")
    openrouter_api_key: SecretStr = Field(
        min_length=1, validation_alias="OPENROUTER_API_KEY"
    )
    openrouter_base_url: HttpUrl = Field(validation_alias="OPENROUTER_BASE_URL")
    mistral_api_key: SecretStr = Field(min_length=1, validation_alias="MISTRAL_API_KEY")
    mistral_base_url: HttpUrl = Field(validation_alias="MISTRAL_BASE_URL")

    @field_validator("openrouter_api_key", "mistral_api_key", mode="before")
    @classmethod
    def reject_whitespace_only_api_keys(cls, value: object) -> object:
        if isinstance(value, str) and value.isspace():
            raise ValueError("API credential must not be blank")
        return value


_FIELD_TO_ENVIRONMENT = {
    "main_provider": "MAIN_LLM_PROVIDER",
    "main_model": "MAIN_LLM_MODEL",
    "extraction_provider": "EXTRACTION_LLM_PROVIDER",
    "extraction_model": "EXTRACTION_LLM_MODEL",
    "fallback_provider": "FALLBACK_LLM_PROVIDER",
    "fallback_model": "FALLBACK_LLM_MODEL",
    "judge_provider": "JUDGE_LLM_PROVIDER",
    "judge_model": "JUDGE_LLM_MODEL",
    "openrouter_api_key": "OPENROUTER_API_KEY",
    "openrouter_base_url": "OPENROUTER_BASE_URL",
    "mistral_api_key": "MISTRAL_API_KEY",
    "mistral_base_url": "MISTRAL_BASE_URL",
}
_ENVIRONMENT_NAMES = frozenset(_FIELD_TO_ENVIRONMENT.values())


def _invalid_environment_names(error: ValidationError) -> list[str]:
    names: set[str] = set()
    for detail in error.errors(include_input=False, include_url=False):
        location = str(detail["loc"][0])
        if location in _ENVIRONMENT_NAMES:
            names.add(location)
        elif location in _FIELD_TO_ENVIRONMENT:
            names.add(_FIELD_TO_ENVIRONMENT[location])
    return sorted(names)


def load_model_settings(env_file: Path | None = None) -> ModelSettings:
    selected_env_file = env_file
    if selected_env_file is None:
        configured_env_file = os.environ.get("MODEL_ENV_FILE", "").strip()
        selected_env_file = (
            Path(configured_env_file) if configured_env_file else Path.cwd() / ".env"
        )

    try:
        raw = _RawModelSettings(_env_file=selected_env_file)
    except ValidationError as error:
        names = _invalid_environment_names(error)
        suffix = ", ".join(names) if names else "unknown environment variable"
        raise ModelConfigurationError(f"Invalid model configuration: {suffix}") from None

    return ModelSettings(
        main=ModelRoleSettings(provider=raw.main_provider, model=raw.main_model),
        extraction=ModelRoleSettings(
            provider=raw.extraction_provider, model=raw.extraction_model
        ),
        fallback=ModelRoleSettings(
            provider=raw.fallback_provider, model=raw.fallback_model
        ),
        judge=ModelRoleSettings(provider=raw.judge_provider, model=raw.judge_model),
        openrouter=ProviderConnectionSettings(
            base_url=raw.openrouter_base_url, api_key=raw.openrouter_api_key
        ),
        mistral=ProviderConnectionSettings(
            base_url=raw.mistral_base_url, api_key=raw.mistral_api_key
        ),
    )


def validate_model_configuration(env_file: Path | None = None) -> None:
    from backend.app.models.routing import resolve_model_routes

    resolve_model_routes(load_model_settings(env_file))
