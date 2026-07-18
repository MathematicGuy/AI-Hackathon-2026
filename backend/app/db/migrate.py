"""Idempotent SQL migration runner.

Applies numbered ``*.sql`` files from ``backend/migrations/`` in filename order,
each inside a transaction, recording applied versions in ``schema_migrations``.
Re-running only applies files not yet recorded.
"""

from __future__ import annotations

import logging
from pathlib import Path

from backend.app.config.db_settings import load_data_platform_settings
from backend.app.db.connection import connect
from backend.app.logging_config import configure_logging

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


def split_statements(sql: str) -> list[str]:
    """Split a SQL script into top-level statements.

    Handles line comments (``--``), block comments (``/* */``), single-quoted
    strings, and dollar-quoted strings (``$tag$ ... $tag$``) so semicolons
    inside them do not split a statement.
    """
    statements: list[str] = []
    buf: list[str] = []
    i, n = 0, len(sql)
    in_line_comment = False
    in_block_comment = False
    in_single = False
    dollar_tag: str | None = None

    while i < n:
        ch = sql[i]
        two = sql[i : i + 2]

        if in_line_comment:
            buf.append(ch)
            if ch == "\n":
                in_line_comment = False
            i += 1
            continue
        if in_block_comment:
            buf.append(ch)
            if two == "*/":
                buf.append("/")
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue
        if in_single:
            buf.append(ch)
            if ch == "'":
                in_single = False
            i += 1
            continue
        if dollar_tag is not None:
            if sql.startswith(dollar_tag, i):
                buf.append(dollar_tag)
                i += len(dollar_tag)
                dollar_tag = None
                continue
            buf.append(ch)
            i += 1
            continue

        # Not inside any quoted/comment context.
        if two == "--":
            in_line_comment = True
            buf.append(two)
            i += 2
            continue
        if two == "/*":
            in_block_comment = True
            buf.append(two)
            i += 2
            continue
        if ch == "'":
            in_single = True
            buf.append(ch)
            i += 1
            continue
        if ch == "$":
            end = sql.find("$", i + 1)
            if end != -1 and sql[i + 1 : end].isidentifier() or (
                end != -1 and sql[i + 1 : end] == ""
            ):
                dollar_tag = sql[i : end + 1]
                buf.append(dollar_tag)
                i = end + 1
                continue
        if ch == ";":
            stmt = "".join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
            i += 1
            continue

        buf.append(ch)
        i += 1

    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def _ensure_version_table(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version    text PRIMARY KEY,
            applied_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )


def _applied_versions(conn) -> set[str]:
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    return {row[0] for row in rows}


def pending_migrations(applied: set[str]) -> list[Path]:
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    return [f for f in files if f.stem not in applied]


def migrate() -> list[str]:
    """Apply all pending migrations; return the versions applied this run.

    The connection runs in autocommit mode so each ``conn.transaction()`` block
    is a real top-level transaction that commits on exit.
    """
    applied_now: list[str] = []
    with connect(autocommit=True) as conn:
        _ensure_version_table(conn)
        pending = pending_migrations(_applied_versions(conn))
        for path in pending:
            statements = split_statements(path.read_text(encoding="utf-8"))
            with conn.transaction():
                for stmt in statements:
                    conn.execute(stmt)
                conn.execute(
                    "INSERT INTO schema_migrations (version) VALUES (%s)",
                    (path.stem,),
                )
            applied_now.append(path.stem)
            logger.info("migrate.applied file=%s", path.name)
    return applied_now


def main() -> None:
    configure_logging()
    settings = load_data_platform_settings()
    # safe_target() is password-free by construction.
    logger.info("migrate.target target=%s", settings.safe_target())
    applied = migrate()
    if applied:
        logger.info("migrate.done applied=%d", len(applied))
    else:
        logger.info("migrate.done up_to_date=true")


if __name__ == "__main__":
    main()
