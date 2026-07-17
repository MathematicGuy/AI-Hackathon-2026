from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.config.model_settings import (
    ModelConfigurationError,
    ProviderName,
    _RawModelSettings,
    load_model_settings,
)


REQUIRED_NAMES = (
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


def _values() -> dict[str, str]:
    return {
        "MAIN_LLM_PROVIDER": "openrouter",
        "MAIN_LLM_MODEL": "test-main-model",
        "EXTRACTION_LLM_PROVIDER": "mistral",
        "EXTRACTION_LLM_MODEL": "test-extraction-model",
        "FALLBACK_LLM_PROVIDER": "openrouter",
        "FALLBACK_LLM_MODEL": "test-fallback-model",
        "JUDGE_LLM_PROVIDER": "mistral",
        "JUDGE_LLM_MODEL": "test-judge-model",
        "OPENROUTER_API_KEY": "test-openrouter-secret",
        "OPENROUTER_BASE_URL": "https://openrouter.example/api",
        "MISTRAL_API_KEY": "test-mistral-secret",
        "MISTRAL_BASE_URL": "https://mistral.example/api",
    }


def _write_dotenv(path: Path, values: dict[str, str]) -> Path:
    path.write_text(
        "\n".join(f"{name}={value}" for name, value in values.items()) + "\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture(autouse=True)
def _clear_model_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (*REQUIRED_NAMES, "MODEL_ENV_FILE"):
        monkeypatch.delenv(name, raising=False)


def test_explicit_dotenv_loads_all_roles_and_connections(tmp_path: Path) -> None:
    values = _values()
    settings = load_model_settings(_write_dotenv(tmp_path / "models.env", values))

    assert settings.main.provider is ProviderName.OPENROUTER
    assert settings.main.model == values["MAIN_LLM_MODEL"]
    assert settings.extraction.provider is ProviderName.MISTRAL
    assert settings.extraction.model == values["EXTRACTION_LLM_MODEL"]
    assert settings.fallback.model == values["FALLBACK_LLM_MODEL"]
    assert settings.judge.model == values["JUDGE_LLM_MODEL"]
    assert str(settings.connection_for(ProviderName.OPENROUTER).base_url) == values[
        "OPENROUTER_BASE_URL"
    ]
    assert settings.connection_for(ProviderName.MISTRAL).api_key.get_secret_value() == values[
        "MISTRAL_API_KEY"
    ]


def test_process_environment_overrides_dotenv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    values = _values()
    env_file = _write_dotenv(tmp_path / "models.env", values)
    monkeypatch.setenv("MAIN_LLM_PROVIDER", "mistral")
    monkeypatch.setenv("MAIN_LLM_MODEL", "test-process-model")

    settings = load_model_settings(env_file)

    assert settings.main.provider is ProviderName.MISTRAL
    assert settings.main.model == "test-process-model"


def test_model_env_file_selects_dotenv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    values = _values()
    env_file = _write_dotenv(tmp_path / "selected.env", values)
    monkeypatch.setenv("MODEL_ENV_FILE", str(env_file))

    settings = load_model_settings()

    assert settings.judge.model == values["JUDGE_LLM_MODEL"]


@pytest.mark.parametrize("missing_name", REQUIRED_NAMES)
def test_each_required_missing_variable_is_reported_safely(
    tmp_path: Path, missing_name: str
) -> None:
    values = _values()
    removed_value = values.pop(missing_name)

    with pytest.raises(ModelConfigurationError) as caught:
        load_model_settings(_write_dotenv(tmp_path / "missing.env", values))

    message = str(caught.value)
    assert missing_name in message
    assert removed_value not in message


@pytest.mark.parametrize("blank_name", REQUIRED_NAMES)
def test_each_required_blank_variable_is_reported_safely(
    tmp_path: Path, blank_name: str
) -> None:
    values = _values()
    values[blank_name] = ""

    with pytest.raises(ModelConfigurationError) as caught:
        load_model_settings(_write_dotenv(tmp_path / "blank.env", values))

    assert blank_name in str(caught.value)


@pytest.mark.parametrize(
    ("name", "invalid_value"),
    (
        ("MAIN_LLM_PROVIDER", "test-invalid-provider"),
        ("OPENROUTER_BASE_URL", "test-secret-invalid-url"),
    ),
)
def test_invalid_values_are_sanitized(
    tmp_path: Path, name: str, invalid_value: str
) -> None:
    values = _values()
    values[name] = invalid_value

    with pytest.raises(ModelConfigurationError) as caught:
        load_model_settings(_write_dotenv(tmp_path / "invalid.env", values))

    message = str(caught.value)
    assert name in message
    assert invalid_value not in message


@pytest.mark.parametrize("credential_name", ("OPENROUTER_API_KEY", "MISTRAL_API_KEY"))
@pytest.mark.parametrize("source", ("dotenv", "process"))
def test_whitespace_only_credentials_are_rejected_safely(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    credential_name: str,
    source: str,
) -> None:
    values = _values()
    raw_value = " \t "
    if source == "dotenv":
        values[credential_name] = f'"{raw_value}"'
    else:
        monkeypatch.setenv(credential_name, raw_value)

    with pytest.raises(ModelConfigurationError) as caught:
        load_model_settings(_write_dotenv(tmp_path / "whitespace.env", values))

    message = str(caught.value)
    assert credential_name in message
    assert raw_value not in message


def test_secrets_are_redacted_from_public_and_raw_representations(tmp_path: Path) -> None:
    values = _values()
    env_file = _write_dotenv(tmp_path / "models.env", values)

    public_settings = load_model_settings(env_file)
    raw_settings = _RawModelSettings(_env_file=env_file)

    for secret_name in ("OPENROUTER_API_KEY", "MISTRAL_API_KEY"):
        secret = values[secret_name]
        assert secret not in repr(public_settings)
        assert secret not in repr(raw_settings)
