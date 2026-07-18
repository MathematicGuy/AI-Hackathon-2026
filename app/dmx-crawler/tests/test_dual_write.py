from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dmx_crawler.db import ALLOWED_TASK_TYPES, Database
from dmx_crawler.dual_write import (
    LOCATION_TASK_TYPE,
    DualWriteCoordinator,
    LocationCrawlPayload,
    persist_location_payload,
)
from dmx_crawler.models import (
    CategoryConfig,
    DeliveryInfo,
    LocationConfig,
    LocationSnapshot,
    ProductContent,
    ProductLink,
)


URL = "https://www.dienmayxanh.com/laptop/offline-dual-write"


def _payload() -> LocationCrawlPayload:
    specs = [
        {
            "group": "Bộ nhớ",
            "group_ordinal": 0,
            "label": "RAM",
            "raw_label": "RAM",
            "value": "16 GB",
            "raw_value": "16 GB",
            "value_text": "16 GB",
            "value_number": 16,
            "unit": "GB",
            "item_ordinal": 0,
            "source": "dom",
            "provenance": ["dom"],
        },
        {
            "group": "Kết nối",
            "group_ordinal": 1,
            "label": "Cổng USB",
            "raw_label": "Cổng USB",
            "value": "1 x USB-C",
            "raw_value": "1 x USB-C",
            "value_text": "1 x USB-C",
            "item_ordinal": 0,
            "source": "dom",
            "provenance": ["dom"],
        },
    ]
    groups = [
        {"group": "Bộ nhớ", "ordinal": 0, "items": [dict(specs[0], ordinal=0)]},
        {"group": "Kết nối", "ordinal": 1, "items": [dict(specs[1], ordinal=0)]},
    ]
    content = ProductContent(
        canonical_url=URL,
        category_code="laptop",
        name="Laptop Offline Dual Write - TEST-16",
        brand="Test",
        model="TEST-16",
        source_product_key="offline-dual-write-1",
        product_code="TEST-16",
        specs=specs,
        specs_raw=groups,
        specs_diagnostics={"group_count": 2, "total_item_count": 2, "warnings": []},
        images=["https://example.invalid/one.jpg", "https://example.invalid/two.jpg"],
        stock_status="in_stock",
        stock_raw="Còn hàng",
    )
    snapshot = LocationSnapshot(
        sale_price=19_990_000,
        list_price=21_990_000,
        promotion={"label": "offline"},
        stock_status="in_stock",
        stock_raw="Còn hàng",
        delivery=DeliveryInfo(
            status="in_stock",
            method="Giao hàng",
            eta="Ngày mai",
            raw_text="Offline delivery",
            returned_location={"province_id": 1000, "ward_id": 103296},
        ),
        returned_location={"province_id": 1000, "ward_id": 103296},
    )
    return LocationCrawlPayload(
        link=ProductLink(URL, "laptop", source_product_key="offline-dual-write-1"),
        content=content,
        snapshot=snapshot,
        request_url=URL,
        response_url=URL,
        http_status=200,
        latency_ms=5,
        response_hash="a" * 64,
        response_metadata={"specifications": content.specs_diagnostics},
    )


class DualWriteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.neon = Database(str(root / "neon.db"))
        self.sqlite = Database(str(root / "sqlite.db"))
        self.category = CategoryConfig("laptop", "Laptop", "https://www.dienmayxanh.com/laptop", "/laptop/")
        self.location = LocationConfig(
            "hanoi-cau-giay",
            "Cầu Giấy",
            1000,
            "Hà Nội",
            103296,
            "Phường Cầu Giấy",
            "TEST REPRESENTATIVE LOCATION",
        )
        for database in (self.neon, self.sqlite):
            database.initialize()
            database.seed_configs([self.category], [self.location])

    def tearDown(self) -> None:
        self.neon.close()
        self.sqlite.close()
        self.tempdir.cleanup()

    def _run(self, database: Database, command: str = "test") -> str:
        return database.create_run(command, {"offline": True})

    def _write(self, database: Database, run_id: str, payload: LocationCrawlPayload):
        return persist_location_payload(
            database,
            run_id,
            "hanoi-cau-giay",
            payload,
            returned_location={"province_id": 1000, "ward_id": 103296},
        )

    def test_location_workflow_fetches_once_and_writes_neon_before_sqlite(self) -> None:
        calls: list[str] = []
        fetch_count = 0
        payload = _payload()
        neon_run = self._run(self.neon)
        sqlite_run = self._run(self.sqlite)

        def fetch_parse() -> LocationCrawlPayload:
            nonlocal fetch_count
            fetch_count += 1
            calls.append("fetch")
            return payload

        result = DualWriteCoordinator().execute(
            fetch_parse,
            lambda value: calls.append("neon") or self._write(self.neon, neon_run, value),
            lambda value: calls.append("sqlite") or self._write(self.sqlite, sqlite_run, value),
        )

        self.assertEqual(result.status, "success")
        self.assertEqual(fetch_count, 1)
        self.assertEqual(calls, ["fetch", "neon", "sqlite"])
        for database in (self.neon, self.sqlite):
            self.assertEqual(database.table_count("products"), 1)
            self.assertEqual(database.table_count("product_content_versions"), 1)
            self.assertEqual(database.table_count("product_spec_values"), 2)
            self.assertEqual(database.table_count("media_assets"), 2)
            self.assertEqual(database.table_count("product_version_media"), 2)
            self.assertEqual(database.table_count("product_location_versions"), 1)
            task = database.fetchone("SELECT task_type FROM crawl_tasks")
            self.assertEqual(task["task_type"], LOCATION_TASK_TYPE)
            location = database.fetchone(
                "SELECT sale_price,stock_status,delivery_json FROM product_location_versions"
            )
            self.assertEqual((location["sale_price"], location["stock_status"]), (19_990_000, "in_stock"))
            self.assertIn("Offline delivery", location["delivery_json"])

    def test_neon_failure_does_not_write_sqlite_or_refetch(self) -> None:
        fetch_count = 0
        sqlite_writes = 0

        def fetch_parse() -> LocationCrawlPayload:
            nonlocal fetch_count
            fetch_count += 1
            return _payload()

        def fail_neon(_: LocationCrawlPayload):
            raise RuntimeError("neon failed")

        def write_sqlite(_: LocationCrawlPayload):
            nonlocal sqlite_writes
            sqlite_writes += 1

        result = DualWriteCoordinator().execute(fetch_parse, fail_neon, write_sqlite)
        self.assertEqual(result.status, "neon_failed")
        self.assertEqual(fetch_count, 1)
        self.assertEqual(sqlite_writes, 0)
        self.assertEqual(self.sqlite.table_count("products"), 0)

    def test_sqlite_failure_marks_reconciliation_without_refetch(self) -> None:
        fetch_count = 0
        neon_run = self._run(self.neon)

        def fetch_parse() -> LocationCrawlPayload:
            nonlocal fetch_count
            fetch_count += 1
            return _payload()

        result = DualWriteCoordinator().execute(
            fetch_parse,
            lambda value: self._write(self.neon, neon_run, value),
            lambda _: (_ for _ in ()).throw(RuntimeError("sqlite failed")),
        )
        self.assertEqual(result.status, "reconciliation_required")
        self.assertTrue(result.reconciliation_required)
        self.assertEqual(fetch_count, 1)
        self.assertEqual(self.neon.table_count("products"), 1)
        self.assertEqual(self.sqlite.table_count("products"), 0)

    def test_resume_is_idempotent_for_versions_specs_and_media(self) -> None:
        payload = _payload()
        first = self._write(self.neon, self._run(self.neon, "first"), payload)
        second = self._write(self.neon, self._run(self.neon, "resume"), payload)
        self.assertTrue(first.content_changed)
        self.assertTrue(first.location_changed)
        self.assertFalse(second.content_changed)
        self.assertFalse(second.location_changed)
        self.assertEqual(first.content_version_id, second.content_version_id)
        self.assertEqual(first.location_version_id, second.location_version_id)
        self.assertEqual(self.neon.table_count("products"), 1)
        self.assertEqual(self.neon.table_count("product_content_versions"), 1)
        self.assertEqual(self.neon.table_count("product_spec_values"), 2)
        self.assertEqual(self.neon.table_count("media_assets"), 2)
        self.assertEqual(self.neon.table_count("product_version_media"), 2)
        self.assertEqual(self.neon.table_count("product_location_versions"), 1)
        self.assertEqual(self.neon.table_count("crawl_observations"), 4)

    def test_partial_location_persist_rolls_back_the_product_payload(self) -> None:
        run_id = self._run(self.neon, "atomic rollback")
        with self.assertRaises(KeyError):
            persist_location_payload(self.neon, run_id, "missing-location", _payload())
        self.assertEqual(self.neon.table_count("products"), 0)
        self.assertEqual(self.neon.table_count("product_urls"), 0)
        self.assertEqual(self.neon.table_count("product_content_versions"), 0)
        self.assertEqual(self.neon.table_count("crawl_tasks"), 0)

    def test_task_type_allow_list_rejects_internal_workflow_name(self) -> None:
        self.assertEqual(ALLOWED_TASK_TYPES, {"discover", "common_product", "location_product"})
        run_id = self._run(self.neon)
        for task_type in sorted(ALLOWED_TASK_TYPES):
            self.neon.create_task(run_id, task_type, task_type)
        with self.assertRaises(ValueError):
            self.neon.create_task(run_id, "hanoi" + "_product", "invalid")
        stored = {row["task_type"] for row in self.neon.fetchall("SELECT task_type FROM crawl_tasks")}
        self.assertEqual(stored, ALLOWED_TASK_TYPES)
