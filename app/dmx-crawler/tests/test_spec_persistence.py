from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dmx_crawler.db import Database
from dmx_crawler.models import CategoryConfig, ProductLink
from dmx_crawler.parsers import parse_product_page


ROOT = Path(__file__).parent


def item_shape(item: dict) -> tuple:
    value_boolean = item.get("value_boolean")
    if value_boolean is not None:
        value_boolean = bool(value_boolean)
    return (
        item.get("group", ""),
        int(item.get("group_ordinal", 0)),
        item.get("label", ""),
        item.get("raw_label", item.get("label", "")),
        item.get("value", item.get("value_text", "")),
        item.get("raw_value", item.get("value", item.get("value_text", ""))),
        item.get("value_text", item.get("value", "")),
        item.get("value_number"),
        value_boolean,
        item.get("value_json", {}),
        item.get("unit"),
        int(item.get("item_ordinal", item.get("ordinal", 0))),
        item.get("source", "dom"),
        list(item.get("provenance", item.get("sources", [item.get("source", "dom")]))),
    )


def db_item_shape(row) -> tuple:
    value_boolean = row["value_boolean"]
    if value_boolean is not None:
        value_boolean = bool(value_boolean)
    return (
        row["group_name"],
        int(row["group_ordinal"]),
        row["label"],
        row["raw_label"],
        row["value_text"],
        row["raw_value"],
        row["value_text"],
        row["value_number"],
        value_boolean,
        json.loads(row["value_json"]),
        row["unit"],
        int(row["item_ordinal"]),
        row["source"],
        json.loads(row["provenance_json"]),
    )


class RichSpecificationPersistenceTests(unittest.TestCase):
    @staticmethod
    def rows_for_version(db: Database, version_id: str):
        return db.fetchall(
            """SELECT d.canonical_label AS label,v.group_name,v.group_ordinal,v.raw_label,v.raw_value,
                      v.value_text,v.value_number,v.value_boolean,v.value_json,v.unit,v.item_ordinal,
                      v.source,v.provenance_json
               FROM product_spec_values v
               LEFT JOIN spec_definitions d ON d.id=v.definition_id
               WHERE v.content_version_id=?
               ORDER BY v.group_ordinal,v.item_ordinal,v.id""",
            (version_id,),
        )

    def test_snapshot_and_eav_keep_groups_duplicates_order_and_typed_values(self) -> None:
        payload = json.loads((ROOT / "fixtures/specs_dynamic_response.json").read_text(encoding="utf-8"))
        content = parse_product_page(
            (ROOT / "fixtures/specs_tv_complete.html").read_text(encoding="utf-8"),
            "https://example.test/tivi-fixture",
            "tivi",
            spec_payloads=[payload],
        )
        expected = [item_shape(item) for item in content.specs]
        content.specs = []

        with tempfile.TemporaryDirectory() as tempdir:
            db = Database(str(Path(tempdir) / "specs.db"))
            try:
                db.initialize()
                db.seed_configs(
                    [CategoryConfig(code="tivi", name="Tivi", url="https://example.test/tivi", path_prefix="/tivi/")],
                    [],
                )
                product_id = db.upsert_product(
                    ProductLink(url="https://example.test/tivi-fixture", category_code="tivi", source_product_key="tv-1")
                )
                version_id, changed = db.record_content(product_id, content)
                self.assertTrue(changed)

                snapshot = json.loads(
                    db.fetchone(
                        "SELECT specs_raw_json FROM product_content_versions WHERE id=?", (version_id,)
                    )["specs_raw_json"]
                )
                rows = self.rows_for_version(db, version_id)
                snapshot_items = [item for group in snapshot for item in group["items"]]

                self.assertEqual(len(rows), sum(len(group["items"]) for group in snapshot))
                self.assertEqual([item_shape(item) for item in snapshot_items], expected)
                self.assertEqual([db_item_shape(row) for row in rows], expected)
                self.assertEqual(len(snapshot), 3)
                self.assertEqual(len(rows), 7)
                self.assertEqual(sum(row["raw_label"] == "Công nghệ" for row in rows), 2)
                self.assertEqual(
                    {row["group_name"] for row in rows if row["raw_label"] == "Công nghệ"},
                    {"Hình ảnh", "Âm thanh"},
                )
                self.assertEqual(rows[0]["value_number"], 55.0)
                self.assertEqual(rows[0]["unit"], "inch")
                self.assertEqual(json.loads(rows[6]["value_json"]), ["HDMI 2.1", "eARC"])
                self.assertIn("dom", json.loads(rows[0]["provenance_json"]))

                content.specs_raw[0]["items"][0]["raw_value"] = "55 inches"
                next_version_id, next_changed = db.record_content(product_id, content)
                self.assertTrue(next_changed)
                self.assertNotEqual(next_version_id, version_id)
            finally:
                db.close()

    def test_colon_label_and_json_ld_subset_round_trip_losslessly(self) -> None:
        html = """
          <html><head><script type="application/ld+json">
            {"@type":"Product","name":"Fixture","additionalProperty":[
              {"name":"Cổng giao tiếp","value":"1 x USB 3.2"}
            ]}
          </script></head><body>
          <section class="technical-specifications">
            <h2>Thông số kỹ thuật</h2>
            <h3>Kết nối</h3>
            <ul><li><strong>Cổng giao tiếp:</strong>
              <aside>Cổng giao tiếp: | 1 x USB 3.2</aside>
              <aside>1 x USB 2.0</aside>
            </li></ul>
          </section></body></html>
        """
        content = parse_product_page(html, "https://example.test/tivi-colon", "tivi")
        self.assertEqual(len(content.specs), 1)
        expected_item = content.specs[0]
        self.assertEqual(expected_item["raw_label"], "Cổng giao tiếp:")
        self.assertEqual(expected_item["value_text"], "1 x USB 3.2 1 x USB 2.0")
        self.assertEqual(expected_item["raw_value"], "1 x USB 3.2\n1 x USB 2.0")
        self.assertEqual(expected_item["provenance"], ["dom", "json_ld"])

        with tempfile.TemporaryDirectory() as tempdir:
            db = Database(str(Path(tempdir) / "colon.db"))
            try:
                db.initialize()
                db.seed_configs(
                    [CategoryConfig(code="tivi", name="Tivi", url="https://example.test/tivi", path_prefix="/tivi/")],
                    [],
                )
                product_id = db.upsert_product(
                    ProductLink(url="https://example.test/tivi-colon", category_code="tivi")
                )
                version_id, changed = db.record_content(product_id, content)
                self.assertTrue(changed)
                snapshot = json.loads(
                    db.fetchone(
                        "SELECT specs_raw_json FROM product_content_versions WHERE id=?", (version_id,)
                    )["specs_raw_json"]
                )
                rows = self.rows_for_version(db, version_id)
                self.assertEqual(len(rows), 1)
                self.assertEqual(item_shape(snapshot[0]["items"][0]), item_shape(expected_item))
                self.assertEqual(db_item_shape(rows[0]), item_shape(expected_item))
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()
