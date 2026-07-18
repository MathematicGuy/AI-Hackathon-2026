"""Thin psycopg connection helper driven by :mod:`db_settings`."""

from __future__ import annotations

import contextlib
from collections.abc import Iterator

import psycopg

from backend.app.config.db_settings import (
    DataPlatformSettings,
    load_data_platform_settings,
)


@contextlib.contextmanager
def connect(
    settings: DataPlatformSettings | None = None,
    *,
    autocommit: bool = False,
) -> Iterator[psycopg.Connection]:
    """Open a single connection; close it on exit. Never logs credentials."""
    settings = settings or load_data_platform_settings()
    conn = psycopg.connect(settings.conninfo(), autocommit=autocommit)
    try:
        yield conn
    finally:
        conn.close()
