from __future__ import annotations

import json
import unittest
from pathlib import Path

from dmx_crawler.html import parse_html
from dmx_crawler.parsers import (
    parse_category_page,
    parse_delivery_response,
    parse_product_page,
    parse_specs,
)


FIXTURES = Path(__file__).parent / "fixtures"


def fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class SpecsParserTests(unittest.TestCase):
    def test_extracts_dom_specs_once(self) -> None:
        document = parse_html(fixture_text("product_laptop.html"))
        self.assertEqual(
            [(item["group"], item["label"], item["value"], item["item_ordinal"]) for item in parse_specs(document)],
            [
                ("", "Công nghệ CPU", "Intel Core i3 Alder Lake", 0),
                ("", "RAM", "8 GB DDR4", 1),
            ],
        )

    def test_falls_back_to_json_ld_additional_properties(self) -> None:
        specs = parse_specs(
            parse_html("<html><body></body></html>"),
            {
                "additionalProperty": [
                    {"name": "Loại tivi", "value": "<b>QLED</b> 4K"},
                    {"name": "Dung tích", "value": "500 lít"},
                ]
            },
        )
        self.assertEqual(
            [(item["label"], item["value"], item["source"]) for item in specs],
            [
                ("Loại tivi", "QLED 4K", "json_ld"),
                ("Dung tích", "500 lít", "json_ld"),
            ],
        )


class CategoryParserFixtureTests(unittest.TestCase):
    def test_extracts_and_deduplicates_in_scope_links(self) -> None:
        links = parse_category_page(fixture_text("category_laptop.html"), "laptop")
        self.assertEqual(len(links), 1)
        link = links[0]
        self.assertEqual(link.url, "https://www.dienmayxanh.com/laptop/acer-aspire-a315")
        self.assertEqual(link.category_code, "laptop")
        self.assertEqual(link.source_product_key, "123456")
        self.assertEqual(link.product_code, "LAP001")
        self.assertEqual(link.brand_hint, "Acer")
        self.assertEqual(link.sale_price_hint, 15_990_000)
        self.assertEqual(link.list_price_hint, 17_990_000)
        self.assertEqual(link.sold_hint, 4_400)
        self.assertEqual(link.raw["image"], "/images/acer-card.jpg")


class ProductParserFixtureTests(unittest.TestCase):
    def test_extracts_common_content_and_location_evidence(self) -> None:
        product = parse_product_page(
            fixture_text("product_laptop.html"),
            "https://www.dienmayxanh.com/Laptop/Acer-Aspire-A315?utm_source=test",
            "laptop",
        )
        self.assertEqual(product.canonical_url, "https://www.dienmayxanh.com/laptop/acer-aspire-a315")
        self.assertEqual(product.name, "Laptop Acer Aspire - A315-59-381E")
        self.assertEqual(product.brand, "Acer")
        self.assertEqual(product.model, "A315-59-381E")
        self.assertEqual(product.source_product_key, "123456")
        self.assertEqual(product.rating, 4.7)
        self.assertEqual(product.rating_count, 128)
        self.assertEqual(product.sold_count, 4_400)
        self.assertEqual(product.stock_status, "in_stock")
        self.assertEqual(product.images, ["https://www.dienmayxanh.com/images/acer-a315.jpg"])
        self.assertEqual(len(product.specs), 2)

        location = product.source_location
        self.assertEqual(location["sale_price"], 15_990_000)
        self.assertEqual(location["list_price"], 17_990_000)
        self.assertEqual(location["promotion"]["discount_percent"], 11.0)
        self.assertIn("500.000₫", location["promotion"]["text"])
        self.assertEqual(location["evidence"]["province_id"], 3)
        self.assertEqual(location["evidence"]["ward_id"], 26734)
        self.assertEqual(location["evidence"]["province_name"], "Hồ Chí Minh")

    def test_internal_source_key_is_not_used_as_commercial_model(self) -> None:
        product = parse_product_page(
            """
              <script type="application/ld+json">
                {"@type":"Product","name":"Tivi AI","sku":"123456","mpn":"123456","model":"123456"}
              </script><h1>Tivi AI</h1>
            """,
            "https://example.test/tivi-ai",
            "tivi",
        )
        self.assertEqual(product.source_product_key, "123456")
        self.assertIsNone(product.model)

    def test_digit_leading_commercial_model_is_extracted_from_name(self) -> None:
        product = parse_product_page(
            """
              <script type="application/ld+json">
                {"@type":"Product","name":"Google Tivi TCL AI 4K 65 inch 65P6K","sku":"339737","mpn":"339737"}
              </script><h1>Google Tivi TCL AI 4K 65 inch 65P6K</h1>
            """,
            "https://example.test/tivi-65p6k",
            "tivi",
        )
        self.assertEqual(product.source_product_key, "339737")
        self.assertEqual(product.model, "65P6K")
        self.assertNotEqual(product.model, product.source_product_key)


class DeliveryParserFixtureTests(unittest.TestCase):
    def test_extracts_delivery_and_returned_location(self) -> None:
        delivery = parse_delivery_response(fixture_text("delivery_hcm.json"))
        self.assertEqual(delivery.status, "in_stock")
        self.assertEqual(delivery.address, "TEST REPRESENTATIVE LOCATION, Hồ Chí Minh")
        self.assertEqual(delivery.method, "Giao tận nơi")
        self.assertEqual(delivery.eta, "Trước 18:00 hôm nay")
        self.assertEqual(delivery.returned_location["province_id"], 3)
        self.assertEqual(delivery.returned_location["ward_id"], 26734)

    def test_error_payload_stays_unknown(self) -> None:
        delivery = parse_delivery_response(json.dumps({"code": -1, "msg": "Không có dữ liệu giao hàng"}))
        self.assertEqual(delivery.status, "unknown")
        self.assertEqual(delivery.raw_text, "Không có dữ liệu giao hàng")


if __name__ == "__main__":
    unittest.main()
