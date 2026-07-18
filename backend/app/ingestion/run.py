"""Ingestion entrypoint.

Currently ingests the product catalog only. Knowledge-base and chat-scenario
ingestion are intentionally not wired here yet.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from backend.app.config.db_settings import load_data_platform_settings
from backend.app.db.connection import connect
from backend.app.ingestion.catalog import CATALOG_FILENAME, CatalogStats, ingest_catalog


def _start_run(conn, source_label: str) -> int:
    row = conn.execute(
        "INSERT INTO import_runs (source_label) VALUES (%s) RETURNING id",
        (source_label,),
    ).fetchone()
    conn.commit()
    return row[0]


def _finish_run(conn, run_id: int, status: str, stats: CatalogStats | None) -> None:
    if stats is None:
        conn.execute(
            "UPDATE import_runs SET status = %s, finished_at = now() WHERE id = %s",
            (status, run_id),
        )
    else:
        conn.execute(
            """
            UPDATE import_runs SET
                status = %s,
                finished_at = now(),
                rows_ok = %s,
                rows_skipped = %s,
                rows_error = %s,
                details = %s
            WHERE id = %s
            """,
            (
                status,
                stats.rows_ok,
                stats.skipped,
                stats.errors,
                _details_json(stats),
                run_id,
            ),
        )
    conn.commit()


def _details_json(stats: CatalogStats):
    from psycopg.types.json import Jsonb

    return Jsonb(
        {
            "inserted": stats.inserted,
            "updated": stats.updated,
            "skipped": stats.skipped,
            "errors": stats.errors,
            "per_sheet": stats.per_sheet,
            "error_samples": stats.error_samples,
        }
    )


def _print_summary(stats: CatalogStats) -> None:
    print("\n=== catalog ingestion summary ===")
    print(
        f"inserted={stats.inserted} updated={stats.updated} "
        f"skipped={stats.skipped} errors={stats.errors}"
    )
    for sheet, counts in stats.per_sheet.items():
        print(
            f"  {sheet}: inserted={counts['inserted']} updated={counts['updated']} "
            f"skipped={counts['skipped']} errors={counts['errors']}"
        )
    if stats.error_samples:
        print("  error samples:")
        for sample in stats.error_samples:
            print(f"    - {sample}")


def run_catalog(source_dir: Path) -> int:
    xlsx = source_dir / CATALOG_FILENAME
    if not xlsx.exists():
        print(f"catalog file not found: {xlsx}", file=sys.stderr)
        return 2

    settings = load_data_platform_settings()
    print(f"ingesting catalog from {xlsx} into {settings.safe_target()}")

    with connect() as conn:
        run_id = _start_run(conn, f"catalog:{xlsx.name}")
        try:
            stats = ingest_catalog(
                conn, xlsx, source_file=str(xlsx), import_run_id=run_id
            )
        except Exception as exc:  # noqa: BLE001 - record failure then re-raise
            _finish_run(conn, run_id, "failed", None)
            print(f"ingestion failed: {exc}", file=sys.stderr)
            raise
        _finish_run(conn, run_id, "completed", stats)

    _print_summary(stats)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest data/dataset into Postgres.")
    parser.add_argument(
        "--source",
        default=None,
        help="dataset directory (default: DATASET_DIR / data/dataset)",
    )
    args = parser.parse_args(argv)

    settings = load_data_platform_settings()
    source_dir = Path(args.source) if args.source else settings.dataset_dir
    return run_catalog(source_dir)


if __name__ == "__main__":
    raise SystemExit(main())
