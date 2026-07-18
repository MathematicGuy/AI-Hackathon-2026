from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
import uuid
from pathlib import Path

from dmx_crawler.db import Database
from dmx_crawler.dual_write import record_inventory_skip


class PostgreSQLTaskTypeIntegrationTests(unittest.TestCase):
    """Rollback-only check against an already prepared PostgreSQL database."""

    def test_postgres_and_sqlite_accept_location_product(self) -> None:
        database_url = os.environ.get("DMX_TEST_POSTGRES_URL")
        if not database_url:
            self.skipTest("set DMX_TEST_POSTGRES_URL for rollback-only integration proof")
        try:
            import psycopg
        except ImportError as error:
            raise RuntimeError("psycopg is required when DMX_TEST_POSTGRES_URL is set") from error

        run_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())
        connection = psycopg.connect(database_url)
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO crawler.crawl_runs
                       (id,command,mode,status,arguments_json,started_at)
                       VALUES (%s,%s,%s,%s,%s,now())""",
                    (run_id, "rollback-only task type test", "test", "running", "{}"),
                )
                cursor.execute(
                    """INSERT INTO crawler.crawl_tasks
                       (id,run_id,task_type,target_key,status,max_attempts,available_at,created_at)
                       VALUES (%s,%s,%s,%s,%s,%s,now(),now())""",
                    (task_id, run_id, "location_product", "rollback-only", "queued", 3),
                )
                cursor.execute(
                    "SELECT task_type FROM crawler.crawl_tasks WHERE id=%s",
                    (task_id,),
                )
                self.assertEqual(cursor.fetchone()[0], "location_product")
        finally:
            connection.rollback()
            connection.close()

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "task-type.db"
            sqlite = sqlite3.connect(path)
            try:
                sqlite.execute(
                    "CREATE TABLE crawl_tasks(task_type TEXT NOT NULL CHECK(task_type IN ('discover','common_product','location_product')))"
                )
                sqlite.execute("INSERT INTO crawl_tasks(task_type) VALUES (?)", ("location_product",))
                self.assertEqual(
                    sqlite.execute("SELECT task_type FROM crawl_tasks").fetchone()[0],
                    "location_product",
                )
            finally:
                sqlite.close()

    def test_postgres_inventory_skip_helper_is_rollback_only(self) -> None:
        database_url = os.environ.get("DMX_TEST_POSTGRES_URL")
        if not database_url:
            self.skipTest("set DMX_TEST_POSTGRES_URL for rollback-only integration proof")

        class RollbackProbe(Exception):
            pass

        database = Database(database_url)
        try:
            database.initialize()
            before = {
                "products": database.table_count("products"),
                "tasks": database.table_count("crawl_tasks"),
                "attempts": database.table_count("crawl_attempts"),
                "errors": database.table_count("crawl_errors"),
            }
            with self.assertRaises(RollbackProbe):
                with database.transaction():
                    run_id = database.create_run("rollback-only inventory skip", {"offline": True})
                    result = record_inventory_skip(
                        database, run_id, "hanoi-cau-giay",
                        request_url="https://example.invalid/out-of-stock",
                        response_url="https://example.invalid/out-of-stock",
                        http_status=200,
                        returned_location={"province_id": 1000, "ward_id": 103296},
                    )
                    task = database.fetchone("SELECT task_type,status FROM {crawl_tasks} WHERE id=?", (result.task_id,))
                    attempt = database.fetchone("SELECT outcome,http_status FROM {crawl_attempts} WHERE id=?", (result.attempt_id,))
                    self.assertEqual((task["task_type"], task["status"]), ("location_product", "skipped_out_of_stock"))
                    self.assertEqual((attempt["outcome"], attempt["http_status"]), ("skipped_out_of_stock", 200))
                    self.assertEqual(database.table_count("products"), before["products"])
                    self.assertEqual(database.table_count("crawl_errors"), before["errors"])
                    raise RollbackProbe()
            after = {
                "products": database.table_count("products"),
                "tasks": database.table_count("crawl_tasks"),
                "attempts": database.table_count("crawl_attempts"),
                "errors": database.table_count("crawl_errors"),
            }
            self.assertEqual(after, before)
        finally:
            database.close()
