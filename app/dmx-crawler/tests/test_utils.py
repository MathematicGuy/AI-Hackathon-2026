from __future__ import annotations

import unittest

from dmx_crawler.utils import (
    canonical_product_key,
    canonical_url,
    location_matches,
    parse_price,
    parse_sold_count,
)


class ParsePriceTests(unittest.TestCase):
    def test_common_dmx_price_formats(self) -> None:
        cases = {
            "21.090.000₫": 21_090_000,
            "23,990,000 VND": 23_990_000,
            "23990000.0": 23_990_000,
            "12,5 triệu": 12_500_000,
            "1,2 tỷ": 1_200_000_000,
            "950k": 950_000,
            "1.5m": 1_500_000,
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(parse_price(raw), expected)

    def test_missing_or_non_numeric_price_is_none(self) -> None:
        for raw in (None, "", "Liên hệ", "Contact"):
            with self.subTest(raw=raw):
                self.assertIsNone(parse_price(raw))


class ParseSoldCountTests(unittest.TestCase):
    def test_abbreviated_and_full_counts(self) -> None:
        cases = {
            "Đã bán 4,4k": 4_400,
            "Đã bán 12.345": 12_345,
            "Đã bán 950": 950,
            "Đã bán 1,2 triệu": 1_200_000,
            "2.5k": 2_500,
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(parse_sold_count(raw), expected)

    def test_missing_sold_count_is_none(self) -> None:
        for raw in (None, "", "Không có dữ liệu"):
            with self.subTest(raw=raw):
                self.assertIsNone(parse_sold_count(raw))


class CanonicalUrlTests(unittest.TestCase):
    def test_normalizes_host_path_and_drops_tracking(self) -> None:
        self.assertEqual(
            canonical_url("https://dienmayxanh.com/Laptop//Acer-Aspire/?utm_source=ads#specs"),
            "https://www.dienmayxanh.com/laptop/acer-aspire",
        )

    def test_resolves_relative_product_url(self) -> None:
        self.assertEqual(
            canonical_url("/TIVI/Samsung-QLED/?gclid=abc"),
            "https://www.dienmayxanh.com/tivi/samsung-qled",
        )

    def test_equivalent_urls_produce_same_dedupe_key(self) -> None:
        first = canonical_product_key(canonical_url("/tu-lanh/lg-inverter?utm_campaign=x"))
        second = canonical_product_key(canonical_url("https://dienmayxanh.com/tu-lanh/lg-inverter/"))
        self.assertEqual(first, second)

    def test_source_key_is_authoritative_when_available(self) -> None:
        self.assertEqual(
            canonical_product_key("https://example.invalid/a", "123456"),
            canonical_product_key("https://example.invalid/b", "123456"),
        )


class LocationMatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.requested = {
            "province_id": 3,
            "ward_id": 26734,
            "name": "TP.HCM",
            "province_name": "Hồ Chí Minh",
            "aliases": ["Sài Gòn", "Ho Chi Minh"],
        }

    def test_matches_numeric_id_and_alias_text(self) -> None:
        evidence = {
            "province_id": "3",
            "ward_id": 26734,
            "province_name": "Thành phố Hồ Chí Minh",
        }
        self.assertTrue(location_matches(self.requested, evidence, require_ward=True))

    def test_rejects_wrong_province_even_if_text_looks_right(self) -> None:
        evidence = {"province_id": 1, "province_name": "Hồ Chí Minh"}
        self.assertFalse(location_matches(self.requested, evidence))

    def test_rejects_conflicting_location_text(self) -> None:
        evidence = {"province_id": 3, "location_text": "Giao hàng tại Hà Nội"}
        self.assertFalse(location_matches(self.requested, evidence))

    def test_require_ward_rejects_missing_or_wrong_ward(self) -> None:
        self.assertFalse(location_matches(self.requested, {"province_id": 3}, require_ward=True))
        self.assertFalse(
            location_matches(
                self.requested,
                {"province_id": 3, "ward_id": 999, "province_name": "Hồ Chí Minh"},
                require_ward=True,
            )
        )

    def test_numeric_province_is_sufficient_when_no_text_is_returned(self) -> None:
        self.assertTrue(location_matches(self.requested, {"province_id": 3}))


if __name__ == "__main__":
    unittest.main()


class CaptchaDetectionTests(unittest.TestCase):
    def test_passive_recaptcha_script_is_not_a_challenge(self) -> None:
        from dmx_crawler.utils import is_captcha_or_challenge
        self.assertFalse(is_captcha_or_challenge('<input type="hidden" name="g-recaptcha-response"><script src="https://www.google.com/recaptcha/api.js"></script><h1>Product</h1>'))

    def test_visible_challenge_is_blocked(self) -> None:
        from dmx_crawler.utils import is_captcha_or_challenge
        self.assertTrue(is_captcha_or_challenge('<title>Verify you are human</title><div class="g-recaptcha">Captcha</div>'))


class ModelExtractionTests(unittest.TestCase):
    def test_prefers_alphanumeric_model_token(self) -> None:
        from dmx_crawler.utils import extract_model
        self.assertEqual(extract_model('Smart Tivi Neo QLED Samsung AI 4K 55 inch QA55QN80F'), 'QA55QN80F')
        self.assertEqual(extract_model('Google Tivi TCL AI 4K 65 inch 65P6K'), '65P6K')
        self.assertEqual(
            extract_model('Tủ lạnh Toshiba Inverter 460 lít Side By Side GR-RS600WI-PMV(37)-SG'),
            'GR-RS600WI-PMV(37)-SG',
        )

    def test_numeric_internal_id_is_not_a_model_fallback(self) -> None:
        from dmx_crawler.utils import extract_model
        self.assertIsNone(extract_model('Tivi AI', '339737'))
