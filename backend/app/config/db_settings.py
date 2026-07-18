"""Environment-owned database, ingestion, and embedding settings.

Mirrors the pattern in ``model_settings.py``: a Pydantic settings object that
reads only from the environment, keeps secrets in ``SecretStr``, and never
hard-codes hosts, credentials, or paths.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DataPlatformSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
        env_ignore_empty=True,
        hide_input_in_errors=True,
    )

    # --- PostgreSQL connection -------------------------------------------------
    # A full DATABASE_URL wins when provided; otherwise discrete parts are used.
    database_url: str | None = Field(default=None, validation_alias="DATABASE_URL")
    postgres_host: str = Field(default="localhost", validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, validation_alias="POSTGRES_PORT")
    postgres_db: str = Field(default="advisor", validation_alias="POSTGRES_DB")
    postgres_user: str = Field(default="advisor", validation_alias="POSTGRES_USER")
    postgres_password: SecretStr = Field(
        default=SecretStr(""), validation_alias="POSTGRES_PASSWORD"
    )

    # --- Ingestion -------------------------------------------------------------
    dataset_dir: Path = Field(
        default=Path("data/dataset"), validation_alias="DATASET_DIR"
    )
    processed_dir: Path = Field(
        default=Path("data/processed"), validation_alias="PROCESSED_DIR"
    )

    # --- Embeddings (API, provider-agnostic via the openai client) -------------
    embedding_provider: str = Field(
        default="openai", validation_alias="EMBEDDING_PROVIDER"
    )
    embedding_model: str = Field(
        default="text-embedding-3-small", validation_alias="EMBEDDING_MODEL"
    )
    embedding_dim: int = Field(default=1536, validation_alias="EMBEDDING_DIM")
    embedding_api_key: SecretStr = Field(
        default=SecretStr(""), validation_alias="EMBEDDING_API_KEY"
    )
    embedding_base_url: str = Field(
        default="https://api.openai.com/v1", validation_alias="EMBEDDING_BASE_URL"
    )

    # --- API -------------------------------------------------------------------
    # Comma-separated list; empty means no cross-origin browser access.
    advisor_cors_origins: str = Field(
        default="", validation_alias="ADVISOR_CORS_ORIGINS"
    )

    def conninfo(self) -> str:
        """libpq connection string. Includes the password; never log this value."""
        if self.database_url:
            return self.database_url
        pw = self.postgres_password.get_secret_value()
        return (
            f"host={self.postgres_host} port={self.postgres_port} "
            f"dbname={self.postgres_db} user={self.postgres_user} password={pw}"
        )

    def safe_target(self) -> str:
        """Password-free description of the target, safe for logs."""
        if self.database_url:
            # Strip credentials if a URL was supplied.
            tail = self.database_url.rsplit("@", 1)[-1]
            return tail
        return f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def embedding_enabled(self) -> bool:
        return bool(self.embedding_api_key.get_secret_value())

    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.advisor_cors_origins.split(",") if o.strip()]


def load_data_platform_settings() -> DataPlatformSettings:
    """Load settings from the process environment."""
    return DataPlatformSettings()
