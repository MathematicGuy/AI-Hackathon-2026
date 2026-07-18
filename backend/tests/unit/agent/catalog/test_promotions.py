import importlib

import pytest


class MissingModule:
    def __init__(self, name):
        self.name = name

    def __getattr__(self, _attribute):
        pytest.fail(f"US-201 {self.name} module is not implemented")


@pytest.fixture
def promotions():
    try:
        return importlib.import_module("backend.app.agent.catalog.promotions")
    except ModuleNotFoundError:
        return MissingModule("promotions")


def test_parse_vnd_accepts_digit_string(promotions):
    assert promotions.parse_vnd("29490000") == 29_490_000


def test_parse_vnd_accepts_int_and_float(promotions):
    assert promotions.parse_vnd(15990000) == 15_990_000
    assert promotions.parse_vnd(15990000.0) == 15_990_000


def test_parse_vnd_accepts_grouped_string(promotions):
    assert promotions.parse_vnd("29.490.000") == 29_490_000
    assert promotions.parse_vnd("29,490,000 đ") == 29_490_000


def test_parse_vnd_rejects_malformed_without_guessing(promotions):
    assert promotions.parse_vnd(None) is None
    assert promotions.parse_vnd("") is None
    assert promotions.parse_vnd("liên hệ") is None
    assert promotions.parse_vnd("null") is None
    assert promotions.parse_vnd(-5) is None


def test_extract_promotion_full_row(promotions):
    info = promotions.extract_promotion(
        {
            "giá gốc": "29490000",
            "giá khuyến mãi": "26990000",
            "khuyến mãi quà": "Phiếu mua hàng Máy lọc không khí/Hút bụi",
        }
    )
    assert info.list_price == 29_490_000
    assert info.sale_price == 26_990_000
    assert info.gift == "Phiếu mua hàng Máy lọc không khí/Hút bụi"
    assert info.discount_percent == pytest.approx(8.5, abs=0.1)


def test_extract_promotion_no_sale_price(promotions):
    info = promotions.extract_promotion(
        {"giá gốc": "10000000", "giá khuyến mãi": None, "khuyến mãi quà": None}
    )
    assert info.list_price == 10_000_000
    assert info.sale_price is None
    assert info.gift is None
    assert info.discount_percent is None


def test_extract_promotion_effective_price(promotions):
    with_sale = promotions.extract_promotion(
        {"giá gốc": "10000000", "giá khuyến mãi": "9000000", "khuyến mãi quà": None}
    )
    without_sale = promotions.extract_promotion(
        {"giá gốc": "10000000", "giá khuyến mãi": None, "khuyến mãi quà": None}
    )
    assert with_sale.effective_price == 9_000_000
    assert without_sale.effective_price == 10_000_000
