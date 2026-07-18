from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dmx_crawler.batch_policy import (
    SKIPPED_OUT_OF_STOCK,
    rank_replacement_candidates,
    revise_locked_selection,
    run_inventory_batch,
)
from dmx_crawler.db import Database
from dmx_crawler.dual_write import record_inventory_skip
from dmx_crawler.models import CategoryConfig, LocationConfig


def item(url: str, source_key: str, model: str, *, brand: str = "HP", stock: str = "listed_with_hanoi_price"):
    return {
        "url": url,
        "category": "laptop",
        "source_product_key": source_key,
        "model_hint": model,
        "title": f"Laptop {brand} {model}",
        "brand": brand,
        "selection_type": "Học tập – Văn phòng",
        "memberships": ["Loại: Học tập – Văn phòng"],
        "price_band": "low",
        "sale_price": 18_990_000,
        "listing_location_evidence": "confirmed_session",
        "stock_status": stock,
    }


class BatchPolicyTests(unittest.TestCase):
    def test_two_out_of_stock_items_do_not_stop_the_next_item(self) -> None:
        rows = [item("https://example.invalid/1", "1", "M1"), item("https://example.invalid/2", "2", "M2"), item("https://example.invalid/3", "3", "M3")]
        stocks = {rows[0]["url"]: "out_of_stock", rows[1]["url"]: "out_of_stock", rows[2]["url"]: "in_stock"}
        fetched: list[str] = []
        persisted: list[str] = []
        audited: list[str] = []
        results = {}

        summary = run_inventory_batch(
            rows,
            results,
            lambda row: fetched.append(row["url"]) or {"stock_status": stocks[row["url"]]},
            lambda row, payload: persisted.append(row["url"]) or {"payload": "saved"},
            lambda row, payload: audited.append(row["url"]),
        )

        self.assertEqual(fetched, [row["url"] for row in rows])
        self.assertEqual(persisted, [rows[2]["url"]])
        self.assertEqual(audited, [rows[0]["url"], rows[1]["url"]])
        self.assertEqual(summary.skipped_out_of_stock, 2)
        self.assertEqual(summary.persisted, 1)
        self.assertEqual(results[rows[0]["url"]]["status"], SKIPPED_OUT_OF_STOCK)

    def test_resume_does_not_request_a_skipped_out_of_stock_url(self) -> None:
        rows = [item("https://example.invalid/1", "1", "M1"), item("https://example.invalid/2", "2", "M2")]
        results = {rows[0]["url"]: {"status": SKIPPED_OUT_OF_STOCK}}
        fetched: list[str] = []
        summary = run_inventory_batch(
            rows,
            results,
            lambda row: fetched.append(row["url"]) or {"stock_status": "in_stock"},
            lambda row, payload: {},
            lambda row, payload: self.fail("terminal skipped URL must not be audited again"),
        )
        self.assertEqual(fetched, [rows[1]["url"]])
        self.assertEqual(summary.resumed_terminal, 1)

    def test_inventory_skip_writes_valid_audit_without_product_payload(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Database(str(Path(directory) / "inventory.db"))
            try:
                database.initialize()
                database.seed_configs(
                    [CategoryConfig("laptop", "Laptop", "https://example.invalid/laptop", "/laptop/")],
                    [LocationConfig("hanoi", "Cầu Giấy", 1000, "Hà Nội", 103296, "Cầu Giấy", "TEST")],
                )
                run_id = database.create_run("inventory skip", {})
                for suffix in ("one", "two"):
                    record_inventory_skip(
                        database,
                        run_id,
                        "hanoi",
                        request_url=f"https://example.invalid/{suffix}",
                        response_url=f"https://example.invalid/{suffix}",
                        http_status=200,
                        returned_location={"province_id": 1000, "ward_id": 103296},
                    )
                self.assertEqual(database.table_count("products"), 0)
                self.assertEqual(database.table_count("product_content_versions"), 0)
                self.assertEqual(database.table_count("product_location_versions"), 0)
                self.assertEqual(database.table_count("crawl_errors"), 0)
                tasks = database.fetchall("SELECT task_type,status,finished_at FROM crawl_tasks ORDER BY url")
                self.assertEqual({row["task_type"] for row in tasks}, {"location_product"})
                self.assertEqual({row["status"] for row in tasks}, {SKIPPED_OUT_OF_STOCK})
                self.assertTrue(all(row["finished_at"] for row in tasks))
                attempts = database.fetchall("SELECT outcome,http_status FROM crawl_attempts")
                self.assertEqual([(row["outcome"], row["http_status"]) for row in attempts], [(SKIPPED_OUT_OF_STOCK, 200), (SKIPPED_OUT_OF_STOCK, 200)])
            finally:
                database.close()

    def test_replacement_ranking_rejects_duplicates_and_revision_restores_quota(self) -> None:
        removed_one = item("https://example.invalid/old-1", "old-1", "OLD1")
        removed_two = item("https://example.invalid/old-2", "old-2", "OLD2", brand="Asus")
        retained = item("https://example.invalid/keep", "keep", "KEEP", brand="Dell")
        candidates = [
            item("https://example.invalid/duplicate-key", "keep", "NEW1"),
            item("https://example.invalid/duplicate-model", "new-2", "KEEP"),
            item("https://example.invalid/new-hp", "new-hp", "HPNEW"),
            item("https://example.invalid/new-asus", "new-asus", "ASUSNEW", brand="Asus"),
        ]
        selected = [removed_one, removed_two, retained]
        first = rank_replacement_candidates(candidates, selected, removed_one)[0]
        second = rank_replacement_candidates([row for row in candidates if row["url"] != first["url"]], [first, removed_two, retained], removed_two)[0]
        checkpoint = {"version": 1, "locked_at": "before", "selected": selected, "results": {}}
        revise_locked_selection(checkpoint, {removed_one["url"]: first, removed_two["url"]: second}, created_at="after")

        self.assertEqual(len(checkpoint["selected"]), 3)
        self.assertEqual(len({row["url"] for row in checkpoint["selected"]}), 3)
        self.assertEqual(len(checkpoint["original_selected"]), 3)
        self.assertEqual(len(checkpoint["selection_revisions"]), 2)
        self.assertEqual(checkpoint["results"][removed_one["url"]]["status"], SKIPPED_OUT_OF_STOCK)
        self.assertEqual(checkpoint["results"][first["url"]]["status"], "pending")
        self.assertNotIn("https://example.invalid/duplicate-key", {row["url"] for row in checkpoint["selected"]})
        self.assertNotIn("https://example.invalid/duplicate-model", {row["url"] for row in checkpoint["selected"]})


if __name__ == "__main__":
    unittest.main()
