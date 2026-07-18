from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from backend.app.config.model_settings import (
    ProviderName,
    load_model_settings,
    validate_model_configuration,
)
from backend.app.models.routing import ModelRoutingError, resolve_model_routes


_MODEL_ENVIRONMENT_NAMES = (
    "MAIN_LLM_PROVIDER",
    "MAIN_LLM_MODEL",
    "EXTRACTION_LLM_PROVIDER",
    "EXTRACTION_LLM_MODEL",
    "FALLBACK_LLM_PROVIDER",
    "FALLBACK_LLM_MODEL",
    "JUDGE_LLM_PROVIDER",
    "JUDGE_LLM_MODEL",
    "OPENROUTER_API_KEY",
    "OPENROUTER_BASE_URL",
    "MISTRAL_API_KEY",
    "MISTRAL_BASE_URL",
)

_VALID_ENVIRONMENT = {
    "MAIN_LLM_PROVIDER": "openrouter",
    "MAIN_LLM_MODEL": "sentinel-main-model",
    "EXTRACTION_LLM_PROVIDER": "mistral",
    "EXTRACTION_LLM_MODEL": "sentinel-extraction-model",
    "FALLBACK_LLM_PROVIDER": "mistral",
    "FALLBACK_LLM_MODEL": "sentinel-fallback-model",
    "JUDGE_LLM_PROVIDER": "openrouter",
    "JUDGE_LLM_MODEL": "sentinel-judge-model",
    "OPENROUTER_API_KEY": "sentinel-openrouter-secret",
    "OPENROUTER_BASE_URL": "https://openrouter.invalid/v1",
    "MISTRAL_API_KEY": "sentinel-mistral-secret",
    "MISTRAL_BASE_URL": "https://mistral.invalid/v1",
}


@pytest.fixture(autouse=True)
def isolate_model_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in _MODEL_ENVIRONMENT_NAMES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("MODEL_ENV_FILE", raising=False)


def _dotenv_file(tmp_path: Path, **overrides: str) -> Path:
    values = _VALID_ENVIRONMENT | overrides
    env_file = tmp_path / "model-routing.env"
    env_file.write_text(
        "\n".join(f"{name}={value}" for name, value in values.items()) + "\n",
        encoding="utf-8",
    )
    return env_file


def _routes(tmp_path: Path, **overrides: str):
    settings = load_model_settings(_dotenv_file(tmp_path, **overrides))
    return resolve_model_routes(settings)


def test_intent_and_explanation_share_main_then_fallback_tuple(tmp_path: Path) -> None:
    routes = _routes(tmp_path)

    assert routes.intent is routes.explanation
    assert [(route.provider, route.model) for route in routes.intent] == [
        (ProviderName.OPENROUTER, "sentinel-main-model"),
        (ProviderName.MISTRAL, "sentinel-fallback-model"),
    ]


def test_extraction_uses_extraction_then_fallback(tmp_path: Path) -> None:
    routes = _routes(tmp_path)

    assert [(route.provider, route.model) for route in routes.extraction] == [
        (ProviderName.MISTRAL, "sentinel-extraction-model"),
        (ProviderName.MISTRAL, "sentinel-fallback-model"),
    ]


def test_judge_has_exactly_one_route(tmp_path: Path) -> None:
    routes = _routes(tmp_path)

    assert len(routes.judge) == 1
    assert (routes.judge[0].provider, routes.judge[0].model) == (
        ProviderName.OPENROUTER,
        "sentinel-judge-model",
    )


def test_routes_and_route_collections_are_immutable(tmp_path: Path) -> None:
    routes = _routes(tmp_path)

    assert isinstance(routes.intent, tuple)
    with pytest.raises(FrozenInstanceError):
        routes.intent = ()
    with pytest.raises(FrozenInstanceError):
        routes.intent[0].model = "changed"


@pytest.mark.parametrize(
    ("overrides", "roles"),
    [
        (
            {
                "FALLBACK_LLM_PROVIDER": "openrouter",
                "FALLBACK_LLM_MODEL": "sentinel-main-model",
            },
            ("main", "fallback"),
        ),
        (
            {"FALLBACK_LLM_MODEL": "sentinel-extraction-model"},
            ("extraction", "fallback"),
        ),
    ],
)
def test_duplicate_routes_are_rejected_without_configuration_details(
    tmp_path: Path,
    overrides: dict[str, str],
    roles: tuple[str, str],
) -> None:
    with pytest.raises(ModelRoutingError) as captured:
        _routes(tmp_path, **overrides)

    message = str(captured.value)
    assert all(role in message for role in roles)
    for private_value in (*_VALID_ENVIRONMENT.values(), *overrides.values()):
        assert private_value not in message


def test_complete_bootstrap_returns_none(tmp_path: Path) -> None:
    assert validate_model_configuration(_dotenv_file(tmp_path)) is None


def test_duplicate_bootstrap_fails_before_client_construction(tmp_path: Path) -> None:
    env_file = _dotenv_file(
        tmp_path,
        FALLBACK_LLM_PROVIDER="openrouter",
        FALLBACK_LLM_MODEL="sentinel-main-model",
    )

    with pytest.raises(ModelRoutingError):
        validate_model_configuration(env_file)


def test_route_repr_does_not_expose_credentials(tmp_path: Path) -> None:
    routes = _routes(tmp_path)
    representation = repr(routes)

    assert "sentinel-openrouter-secret" not in representation
    assert "sentinel-mistral-secret" not in representation
