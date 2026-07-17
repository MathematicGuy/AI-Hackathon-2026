from __future__ import annotations

import json
import unittest
import warnings
from pathlib import Path

from dmx_crawler.html import parse_html
from dmx_crawler.parsers import parse_product_page, parse_specification_groups


FIXTURES = Path(__file__).parent / "fixtures"


def fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def complete_shape(groups: list[dict]) -> list[tuple]:
    """Compare every discovered group/item identity and display order."""

    return [
        (
            group["group"],
            group["ordinal"],
            [
                (
                    item["group"],
                    item["group_ordinal"],
                    item["label"],
                    item["value"],
                    item["raw_value"],
                    item["item_ordinal"],
                    item["source"],
                )
                for item in group["items"]
            ],
        )
        for group in groups
    ]


class CompleteSpecificationFixtureTests(unittest.TestCase):
    def test_laptop_merges_dom_embedded_json_and_json_ld_without_losing_order(self) -> None:
        product = parse_product_page(
            fixture_text("specs_laptop_complete.html"),
            "https://example.test/laptop-fixture",
            "laptop",
        )
        self.assertEqual(
            complete_shape(product.specs_raw),
            [
                (
                    "Bộ xử lý",
                    0,
                    [
                        ("Bộ xử lý", 0, "Công nghệ", "AMD Ryzen 5 - 7520U", "AMD Ryzen 5 - 7520U", 0, "dom"),
                        ("Bộ xử lý", 0, "Số nhân", "4", "4", 1, "dom"),
                    ],
                ),
                (
                    "Bộ nhớ",
                    1,
                    [
                        ("Bộ nhớ", 1, "RAM", "16 GB", "16 GB", 0, "dom"),
                        ("Bộ nhớ", 1, "Công nghệ", "LPDDR5", "LPDDR5", 1, "dom"),
                        ("Bộ nhớ", 1, "Ổ cứng", "512 GB SSD NVMe", "512 GB SSD NVMe", 2, "embedded_json"),
                    ],
                ),
                (
                    "Thông số bổ sung",
                    2,
                    [("Thông số bổ sung", 2, "Trọng lượng", "1.45 kg", "1.45 kg", 0, "json_ld")],
                ),
            ],
        )
        self.assertEqual(product.specs_diagnostics["group_count"], 3)
        self.assertEqual(product.specs_diagnostics["total_item_count"], 6)
        self.assertEqual(product.specs_diagnostics["source_item_counts"], {"dom": 4, "api": 0, "embedded_json": 2, "json_ld": 2})
        ram = next(item for item in product.specs if item["label"] == "RAM")
        self.assertEqual(ram["sources"], ["dom", "embedded_json", "json_ld"])
        self.assertEqual((ram["value_number"], ram["unit"]), (16, "GB"))

    def test_closed_tv_accordions_table_and_div_rows_plus_dynamic_payload(self) -> None:
        payload = json.loads(fixture_text("specs_dynamic_response.json"))
        result = parse_specification_groups(
            parse_html(fixture_text("specs_tv_complete.html")),
            api_payloads=[payload],
        )
        self.assertEqual(
            complete_shape(result.groups),
            [
                (
                    "Hình ảnh",
                    0,
                    [
                        ("Hình ảnh", 0, "Kích cỡ màn hình", "55 inch", "55 inch", 0, "dom"),
                        ("Hình ảnh", 0, "Độ phân giải", "4K (Ultra HD)", "4K (Ultra HD)", 1, "dom"),
                        ("Hình ảnh", 0, "Công nghệ", "Mini LED", "Mini LED", 2, "dom"),
                    ],
                ),
                (
                    "Âm thanh",
                    1,
                    [
                        ("Âm thanh", 1, "Công nghệ", "Dolby Atmos", "Dolby Atmos", 0, "dom"),
                        ("Âm thanh", 1, "Tổng công suất loa", "40 W", "40 W", 1, "dom"),
                    ],
                ),
                (
                    "Kết nối",
                    2,
                    [
                        ("Kết nối", 2, "Bluetooth", "5.3", "5.3", 0, "api"),
                        ("Kết nối", 2, "Cổng HDMI", "HDMI 2.1; eARC", '["HDMI 2.1","eARC"]', 1, "api"),
                    ],
                ),
            ],
        )
        self.assertEqual(result.diagnostics["item_counts"], [
            {"group": "Hình ảnh", "group_ordinal": 0, "item_count": 3},
            {"group": "Âm thanh", "group_ordinal": 1, "item_count": 2},
            {"group": "Kết nối", "group_ordinal": 2, "item_count": 2},
        ])
        self.assertEqual(result.diagnostics["total_item_count"], 7)
        self.assertEqual(sum(item["label"] == "Công nghệ" for item in result.items), 2)

    def test_refrigerator_dl_and_div_rows_preserve_every_item(self) -> None:
        result = parse_specification_groups(parse_html(fixture_text("specs_refrigerator_complete.html")))
        self.assertEqual(
            complete_shape(result.groups),
            [
                (
                    "Thông tin chung",
                    0,
                    [
                        ("Thông tin chung", 0, "Dung tích sử dụng", "510 lít", "510 lít", 0, "dom"),
                        ("Thông tin chung", 0, "Kiểu tủ", "Multi Door", "Multi Door", 1, "dom"),
                    ],
                ),
                (
                    "Tiện ích",
                    1,
                    [
                        ("Tiện ích", 1, "Lấy nước ngoài", "Có", "Có", 0, "dom"),
                        ("Tiện ích", 1, "Làm đá tự động", "Không", "Không", 1, "dom"),
                    ],
                ),
            ],
        )
        self.assertEqual(result.diagnostics["total_item_count"], 4)
        self.assertEqual([item["value_boolean"] for item in result.groups[1]["items"]], [True, False])

    def test_standalone_closed_details_is_detected_without_css_markers(self) -> None:
        result = parse_specification_groups(
            parse_html("<details><summary>Nguồn điện</summary><dl><dt>Điện áp</dt><dd>220 V</dd></dl></details>")
        )
        self.assertEqual(
            complete_shape(result.groups),
            [("Nguồn điện", 0, [("Nguồn điện", 0, "Điện áp", "220 V", "220 V", 0, "dom")])],
        )

    def test_snapshot_and_flat_eav_view_represent_the_same_complete_set(self) -> None:
        product = parse_product_page(
            fixture_text("specs_laptop_complete.html"),
            "https://example.test/laptop-fixture",
            "laptop",
        )
        snapshot = [
            (item["group"], item["group_ordinal"], item["label"], item["value"], item["raw_value"], item["item_ordinal"], item["source"])
            for group in product.specs_raw
            for item in group["items"]
        ]
        flattened = [
            (item["group"], item["group_ordinal"], item["label"], item["value"], item["raw_value"], item["item_ordinal"], item["source"])
            for item in product.specs
        ]
        self.assertEqual(flattened, snapshot)

    def test_incomplete_recognized_markup_emits_warning_and_diagnostics(self) -> None:
        html = """
          <section class="product-specifications">
            <h2>Thông số kỹ thuật</h2>
            <div class="spec-row"><span class="label">Thiếu giá trị</span></div>
          </section>
        """
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = parse_specification_groups(parse_html(html))
        self.assertEqual(result.items, [])
        self.assertEqual(result.diagnostics["rows_missing_value"], 1)
        self.assertGreaterEqual(len(result.diagnostics["warnings"]), 1)
        self.assertGreaterEqual(len(caught), 1)

    def test_unique_dom_label_keeps_primary_value_and_records_source_difference(self) -> None:
        html = """
          <section class="product-specifications">
            <h3>Kết nối</h3>
            <ul><li><strong>Bluetooth</strong><aside>5.2</aside></li></ul>
            <script type="application/json">
              {"specifications":[{"group":"Kết nối","items":[{"label":"Bluetooth","value":"5.3"}]}]}
            </script>
          </section>
        """
        result = parse_specification_groups(parse_html(html))
        self.assertEqual([(item["value"], item["source"]) for item in result.items], [("5.2", "dom")])
        self.assertEqual(result.items[0]["provenance"], ["dom", "embedded_json"])
        self.assertEqual(len(result.diagnostics["conflicts"]), 1)
        self.assertEqual(result.diagnostics["conflicts"][0]["primary_value"], "5.2")
        self.assertEqual(result.diagnostics["conflicts"][0]["incoming_value"], "5.3")


    def test_anonymous_div_colon_and_multiple_value_nodes_are_lossless(self) -> None:
        html = """
          <section class="technical-specifications">
            <h2>Thông số kỹ thuật</h2>
            <div>
              <div><span>Cổng hỗ trợ</span><span>HDMI 2.1</span><span>USB-C</span></div>
            </div>
            <ul>
              <li>Trọng lượng: 1.20 kg</li>
              <li><strong>Chuẩn kết nối</strong><aside>Wi-Fi 6</aside><aside>Bluetooth 5.3</aside></li>
            </ul>
          </section>
        """
        result = parse_specification_groups(parse_html(html))
        self.assertEqual(
            [(item["label"], item["value"], item["raw_value"], item["item_ordinal"]) for item in result.items],
            [
                ("Cổng hỗ trợ", "HDMI 2.1 USB-C", "HDMI 2.1\nUSB-C", 0),
                ("Trọng lượng", "1.20 kg", "1.20 kg", 1),
                ("Chuẩn kết nối", "Wi-Fi 6 Bluetooth 5.3", "Wi-Fi 6\nBluetooth 5.3", 2),
            ],
        )
        for item in result.items:
            self.assertNotIn("|", item["value"])
            self.assertNotIn("|", item["raw_value"])

    def test_value_legitimately_starting_with_label_is_cleaned_only_once(self) -> None:
        html = """
          <section class="technical-specifications">
            <h2>Thông số kỹ thuật</h2>
            <h3>Bộ xử lý</h3>
            <ul><li><strong>Bộ xử lý:</strong><aside>Bộ xử lý: | Bộ xử lý AiPQ</aside></li></ul>
          </section>
        """
        result = parse_specification_groups(parse_html(html))
        self.assertEqual(len(result.items), 1)
        self.assertEqual(
            (
                result.items[0]["label"],
                result.items[0]["raw_label"],
                result.items[0]["value"],
                result.items[0]["raw_value"],
            ),
            ("Bộ xử lý", "Bộ xử lý:", "Bộ xử lý AiPQ", "Bộ xử lý AiPQ"),
        )

    def test_dom_colon_multiline_and_json_ld_subset_merge_without_empty_group(self) -> None:
        html = """
          <html><head><script type="application/ld+json">
            {"@type":"Product","additionalProperty":[
              {"name":"CÔNG NGHỆ CPU：","value":"AMD Ryzen 5 - 7520U"},
              {"name":"Cổng giao tiếp","value":"1 x USB 3.2."}
            ]}
          </script></head><body>
          <section class="product-specifications">
            <h2>Thông số kỹ thuật</h2>
            <h3>Bộ xử lý</h3>
            <ul><li><strong>Công nghệ CPU:</strong><aside>Công nghệ CPU: | AMD Ryzen 5 - 7520U</aside></li></ul>
            <h3>Kết nối</h3>
            <ul><li><strong>Cổng giao tiếp:</strong>
              <aside>Cổng giao tiếp: | 1 x USB 3.2.</aside>
              <aside>1 x USB 2.0</aside><aside>HDMI 1.4</aside>
            </li></ul>
          </section></body></html>
        """
        result = parse_specification_groups(parse_html(html))
        self.assertEqual([group["group"] for group in result.groups], ["Bộ xử lý", "Kết nối"])
        self.assertEqual((result.diagnostics["group_count"], result.diagnostics["total_item_count"]), (2, 2))
        self.assertEqual(result.diagnostics["empty_groups"], [])
        self.assertEqual(
            result.diagnostics["source_item_counts"],
            {"dom": 2, "api": 0, "embedded_json": 0, "json_ld": 2},
        )
        merge = result.diagnostics["merge_diagnostics"]
        self.assertEqual(
            (merge["merged_count"], merge["added_count"], merge["ambiguous_count"]),
            (2, 0, 0),
        )
        self.assertEqual([event["action"] for event in merge["events"]], ["merged", "merged"])
        self.assertTrue(all(item["source"] == "dom" for item in result.items))
        cpu, ports = result.items
        self.assertEqual((cpu["label"], cpu["raw_label"], cpu["value"], cpu["raw_value"]), (
            "Công nghệ CPU", "Công nghệ CPU:", "AMD Ryzen 5 - 7520U", "AMD Ryzen 5 - 7520U"
        ))
        self.assertEqual(cpu["provenance"], ["dom", "json_ld"])
        self.assertEqual(ports["label"], "Cổng giao tiếp")
        self.assertEqual(ports["value"], "1 x USB 3.2. 1 x USB 2.0 HDMI 1.4")
        self.assertEqual(ports["raw_value"], "1 x USB 3.2.\n1 x USB 2.0\nHDMI 1.4")
        self.assertEqual(ports["provenance"], ["dom", "json_ld"])
        self.assertNotIn("Cổng giao tiếp", ports["value"])
        self.assertNotIn("|", ports["value"])
        self.assertNotIn("|", ports["raw_value"])
        differences = result.diagnostics["merge_diagnostics"]["value_differences"]
        self.assertEqual([(item["label"], item["value_relation"]) for item in differences], [
            ("Cổng giao tiếp", "supplemental_subset")
        ])

    def test_duplicate_label_uses_value_then_warns_when_still_ambiguous(self) -> None:
        html = """
          <html><head><script type="application/ld+json">
            {"@type":"Product","additionalProperty":[
              {"name":"Công nghệ:","value":"dolby atmos"},
              {"name":"Công nghệ","value":"AI"}
            ]}
          </script></head><body><section class="technical-specifications">
            <h2>Thông số kỹ thuật</h2>
            <h3>Hình ảnh</h3><ul><li><strong>Công nghệ</strong><aside>Mini LED</aside></li></ul>
            <h3>Âm thanh</h3><ul><li><strong>Công nghệ:</strong><aside>Dolby Atmos</aside></li></ul>
          </section></body></html>
        """
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = parse_specification_groups(parse_html(html))
        self.assertEqual([group["group"] for group in result.groups], ["Hình ảnh", "Âm thanh"])
        self.assertEqual(len(result.items), 2)
        image, audio = result.items
        self.assertEqual(image["provenance"], ["dom"])
        self.assertEqual((audio["value"], audio["provenance"]), ("Dolby Atmos", ["dom", "json_ld"]))
        self.assertEqual(len(result.diagnostics["ambiguous_merges"]), 1)
        ambiguous = result.diagnostics["ambiguous_merges"][0]
        self.assertEqual(ambiguous["incoming_value"], "AI")
        self.assertEqual(ambiguous["candidate_groups"], ["Hình ảnh", "Âm thanh"])
        merge = result.diagnostics["merge_diagnostics"]
        self.assertEqual(
            (merge["merged_count"], merge["added_count"], merge["ambiguous_count"]),
            (1, 0, 1),
        )
        self.assertEqual(
            [(event["action"], event["incoming_value"]) for event in merge["events"]],
            [("merged", "dolby atmos"), ("ambiguous", "AI")],
        )
        self.assertTrue(result.diagnostics["warnings"])
        self.assertTrue(caught)

    def test_equal_duplicate_labels_remain_distinct_and_supplement_is_ambiguous(self) -> None:
        html = """
          <html><head><script type="application/ld+json">
            {"@type":"Product","additionalProperty":[
              {"name":"Chế độ","value":"Tự động"}
            ]}
          </script></head><body><section class="technical-specifications">
            <h2>Thông số kỹ thuật</h2>
            <h3>Hình ảnh</h3><ul><li><strong>Chế độ</strong><aside>Tự động</aside></li></ul>
            <h3>Âm thanh</h3><ul><li><strong>Chế độ</strong><aside>Tự động</aside></li></ul>
            <h3>Kết nối</h3><ul>
              <li><strong>Cổng</strong><aside>USB-A</aside></li>
              <li><strong>Cổng</strong><aside>USB-C</aside></li>
            </ul>
          </section></body></html>
        """
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = parse_specification_groups(parse_html(html))
        self.assertEqual(
            [(item["group"], item["label"], item["value"]) for item in result.items],
            [
                ("Hình ảnh", "Chế độ", "Tự động"),
                ("Âm thanh", "Chế độ", "Tự động"),
                ("Kết nối", "Cổng", "USB-A"),
                ("Kết nối", "Cổng", "USB-C"),
            ],
        )
        self.assertTrue(all(item["provenance"] == ["dom"] for item in result.items))
        merge = result.diagnostics["merge_diagnostics"]
        self.assertEqual(
            (merge["merged_count"], merge["added_count"], merge["ambiguous_count"]),
            (0, 0, 1),
        )
        self.assertEqual(merge["events"][0]["candidate_groups"], ["Hình ảnh", "Âm thanh"])

    def test_typed_values_are_conservative_and_support_compound_units(self) -> None:
        html = """
          <section class="technical-specifications"><h2>Thông số kỹ thuật</h2><h3>Đo lường</h3>
          <table>
            <tr><th>RAM</th><td>16 GB</td></tr>
            <tr><th>Tần số quét</th><td>60 Hz</td></tr>
            <tr><th>Kích cỡ màn hình</th><td>65 inch</td></tr>
            <tr><th>Điện năng</th><td>528 kWh/năm</td></tr>
            <tr><th>Độ phân giải</th><td>4K</td></tr>
            <tr><th>Cổng USB</th><td>1 x USB</td></tr>
          </table></section>
        """
        result = parse_specification_groups(parse_html(html))
        self.assertEqual(len(result.groups), 1)
        self.assertEqual(len(result.items), 6)
        self.assertEqual(
            [item["label"] for item in result.items],
            ["RAM", "Tần số quét", "Kích cỡ màn hình", "Điện năng", "Độ phân giải", "Cổng USB"],
        )
        actual = {
            item["label"]: (item["value_text"], item["value_number"], item["unit"])
            for item in result.items
        }
        self.assertEqual(actual, {
            "RAM": ("16 GB", 16, "GB"),
            "Tần số quét": ("60 Hz", 60, "Hz"),
            "Kích cỡ màn hình": ("65 inch", 65, "inch"),
            "Điện năng": ("528 kWh/năm", 528, "kWh/năm"),
            "Độ phân giải": ("4K", None, None),
            "Cổng USB": ("1 x USB", None, None),
        })

    def test_closed_details_with_anonymous_rows_is_detected_without_viewport_state(self) -> None:
        html = """
          <details>
            <summary>Nguồn điện</summary>
            <div><span>Điện áp</span><span>220 V</span></div>
          </details>
        """
        result = parse_specification_groups(parse_html(html))
        self.assertEqual(
            [(item["group"], item["label"], item["value"]) for item in result.items],
            [("Nguồn điện", "Điện áp", "220 V")],
        )

    def test_nested_api_groups_are_found_without_a_payload_shape_allowlist(self) -> None:
        payload = {
            "data": {
                "groups": [
                    {"groupName": "Tính năng mới", "items": [{"label": "Chế độ", "value": "Eco"}]}
                ]
            }
        }
        result = parse_specification_groups(parse_html("<html></html>"), api_payloads=[payload])
        self.assertEqual(
            [(group["group"], [(item["label"], item["value"]) for item in group["items"]]) for group in result.groups],
            [("Tính năng mới", [("Chế độ", "Eco")])],
        )

    def test_json_ld_product_inside_graph_is_discovered_without_explicit_argument(self) -> None:
        html = """
          <script type="application/ld+json">
            {"@context":"https://schema.org","@graph":[
              {"@type":"BreadcrumbList","itemListElement":[]},
              {"@type":"Product","name":"Graph fixture","additionalProperty":[
                {"@type":"PropertyValue","name":"Công suất","value":"120 W"}
              ]}
            ]}
          </script>
        """
        result = parse_specification_groups(parse_html(html))
        self.assertEqual([(item["label"], item["value"], item["source"]) for item in result.items], [("Công suất", "120 W", "json_ld")])


if __name__ == "__main__":
    unittest.main()
