from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from dmx_crawler.db import Database
from dmx_crawler.models import (
    CategoryConfig,
    DeliveryInfo,
    LocationConfig,
    LocationSnapshot,
    ProductContent,
    ProductLink,
)


class DatabaseDedupAndScdTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "test.db"
        self.db = Database(str(self.db_path))
        self.db.initialize()
        self.db.seed_configs(
            [
                CategoryConfig(
                    code="laptop",
                    name="Laptop",
                    url="https://www.dienmayxanh.com/laptop",
                    path_prefix="/laptop/",
                )
            ],
            [
                LocationConfig(
                    code="hcm",
                    name="TP.HCM",
                    province_id=3,
                    province_name="Hồ Chí Minh",
                    ward_id=26734,
                    ward_name="Phường Bến Nghé",
                    address="TEST HCM LOCATION",
                    aliases=("Sài Gòn",),
                ),
                LocationConfig(
                    code="hanoi",
                    name="Hà Nội",
                    province_id=1,
                    province_name="Hà Nội",
                    ward_id=1,
                    ward_name="Phường Trúc Bạch",
                    address="TEST HANOI LOCATION",
                ),
            ],
        )

    def tearDown(self) -> None:
        self.db.close()
        self.tempdir.cleanup()

    def _product(self, source_key: str = "123456") -> tuple[str, ProductContent]:
        product_id = self.db.upsert_product(
            ProductLink(
                url="https://www.dienmayxanh.com/laptop/acer-a315",
                category_code="laptop",
                source_product_key=source_key,
            )
        )
        content = ProductContent(
            canonical_url="https://www.dienmayxanh.com/laptop/acer-a315",
            category_code="laptop",
            name="Laptop Acer Aspire - A315-59-381E",
            brand="Acer",
            model="A315-59-381E",
            source_product_key=source_key,
            rating=4.7,
            rating_count=128,
            sold_count=4_400,
            specs=[
                {"label": "Công nghệ CPU", "value": "Intel Core i3"},
                {"label": "RAM", "value": "8 GB"},
            ],
            specs_raw={"Công nghệ CPU": "Intel Core i3", "RAM": "8 GB"},
            images=["https://cdn.tgdd.vn/acer.jpg"],
            stock_status="in_stock",
            stock_raw="Còn hàng",
        )
        return product_id, content

    def test_upsert_deduplicates_canonical_url_variants(self) -> None:
        first = self.db.upsert_product(
            ProductLink(
                url="https://dienmayxanh.com/Laptop/Acer-A315/?utm_source=one",
                category_code="laptop",
            )
        )
        second = self.db.upsert_product(
            ProductLink(
                url="https://www.dienmayxanh.com/laptop/acer-a315?gclid=two",
                category_code="laptop",
            )
        )
        self.assertEqual(first, second)
        self.assertEqual(self.db.table_count("products"), 1)
        self.assertEqual(
            self.db.fetchone("SELECT COUNT(*) AS n FROM product_urls")["n"],
            1,
        )

    def test_source_product_key_prevents_duplicate_after_url_changes(self) -> None:
        first = self.db.upsert_product(
            ProductLink(
                url="https://www.dienmayxanh.com/laptop/old-slug",
                category_code="laptop",
                source_product_key="sku-stable",
            )
        )
        second = self.db.upsert_product(
            ProductLink(
                url="https://www.dienmayxanh.com/laptop/new-slug",
                category_code="laptop",
                source_product_key="sku-stable",
            )
        )
        self.assertEqual(first, second)
        self.assertEqual(self.db.table_count("products"), 1)
        row = self.db.fetchone("SELECT canonical_url FROM products WHERE id=?", (first,))
        self.assertEqual(row["canonical_url"], "https://www.dienmayxanh.com/laptop/new-slug")
        self.assertEqual(self.db.fetchone("SELECT COUNT(*) AS n FROM product_urls")["n"], 2)

    def test_content_scd2_reuses_unchanged_and_closes_changed_version(self) -> None:
        product_id, content = self._product()
        first_id, first_changed = self.db.record_content(product_id, content, response_hash="body-a")
        same_id, same_changed = self.db.record_content(product_id, content, response_hash="body-a")
        second_id, second_changed = self.db.record_content(
            product_id,
            replace(content, sold_count=4_500),
            response_hash="body-b",
        )

        self.assertTrue(first_changed)
        self.assertFalse(same_changed)
        self.assertEqual(same_id, first_id)
        self.assertTrue(second_changed)
        self.assertNotEqual(second_id, first_id)

        versions = self.db.fetchall(
            "SELECT id, sold_count, valid_to FROM product_content_versions WHERE product_id=?",
            (product_id,),
        )
        self.assertEqual(len(versions), 2)
        current = [row for row in versions if row["valid_to"] is None]
        closed = [row for row in versions if row["valid_to"] is not None]
        self.assertEqual(len(current), 1)
        self.assertEqual(current[0]["id"], second_id)
        self.assertEqual(current[0]["sold_count"], 4_500)
        self.assertEqual(len(closed), 1)
        self.assertEqual(closed[0]["id"], first_id)
        self.assertEqual(
            self.db.fetchone(
                "SELECT consecutive_unchanged FROM product_crawl_state WHERE product_id=?",
                (product_id,),
            )["consecutive_unchanged"],
            0,
        )

    def test_attempt_persists_http_status_and_spec_diagnostics(self) -> None:
        attempt_id = self.db.record_attempt(
            None,
            1,
            "2026-07-17T00:00:00+00:00",
            "success",
            "https://example.test/product",
            response_url="https://example.test/product",
            http_status=200,
            latency_ms=17,
            response_metadata={
                "http": {"transport_attempt_count": 1},
                "specifications": {
                    "group_count": 6,
                    "total_item_count": 28,
                    "warnings": [],
                    "merge_diagnostics": {"merged_count": 28},
                },
            },
        )
        row = self.db.fetchone("SELECT * FROM crawl_attempts WHERE id=?", (attempt_id,))
        self.assertEqual((row["http_status"], row["latency_ms"], row["outcome"]), (200, 17, "success"))
        metadata = json.loads(row["response_metadata_json"])
        self.assertEqual(metadata["specifications"]["group_count"], 6)
        self.assertEqual(metadata["specifications"]["merge_diagnostics"]["merged_count"], 28)
        self.assertEqual(metadata["http"]["transport_attempt_count"], 1)

    def test_location_scd2_is_independent_per_location(self) -> None:
        product_id, _ = self._product()
        hcm_id = self.db.location_id("hcm")
        hanoi_id = self.db.location_id("hanoi")
        hcm = LocationSnapshot(
            sale_price=15_990_000,
            list_price=17_990_000,
            promotion={"discount_percent": 11},
            stock_status="in_stock",
            stock_raw="Còn hàng",
            delivery=DeliveryInfo(
                status="in_stock",
                address="TEST HCM LOCATION",
                method="Giao tận nơi",
                eta="Hôm nay",
            ),
            returned_location={"province_id": 3, "ward_id": 26734},
        )

        first_id, first_changed = self.db.record_location(product_id, hcm_id, hcm)
        same_id, same_changed = self.db.record_location(product_id, hcm_id, hcm)
        new_id, new_changed = self.db.record_location(
            product_id,
            hcm_id,
            replace(hcm, sale_price=15_490_000),
        )
        hanoi_version, hanoi_changed = self.db.record_location(
            product_id,
            hanoi_id,
            replace(
                hcm,
                sale_price=16_290_000,
                delivery=replace(hcm.delivery, address="TEST HANOI LOCATION"),
                returned_location={"province_id": 1, "ward_id": 1},
            ),
        )

        self.assertTrue(first_changed)
        self.assertFalse(same_changed)
        self.assertEqual(first_id, same_id)
        self.assertTrue(new_changed)
        self.assertNotEqual(first_id, new_id)
        self.assertTrue(hanoi_changed)

        hcm_versions = self.db.fetchall(
            "SELECT id, sale_price, valid_to FROM product_location_versions "
            "WHERE product_id=? AND location_id=?",
            (product_id, hcm_id),
        )
        self.assertEqual(len(hcm_versions), 2)
        self.assertEqual(
            [(row["sale_price"], row["id"]) for row in hcm_versions if row["valid_to"] is None],
            [(15_490_000, new_id)],
        )
        self.assertEqual(len([row for row in hcm_versions if row["valid_to"] is not None]), 1)

        current = self.db.fetchall(
            "SELECT location_id, sale_price FROM product_location_versions "
            "WHERE product_id=? AND valid_to IS NULL ORDER BY location_id",
            (product_id,),
        )
        self.assertEqual(
            {(row["location_id"], row["sale_price"]) for row in current},
            {(hcm_id, 15_490_000), (hanoi_id, 16_290_000)},
        )
        self.assertIn(
            hanoi_version,
            {row["id"] for row in self.db.fetchall("SELECT id FROM product_location_versions")},
        )


if __name__ == "__main__":
    unittest.main()
