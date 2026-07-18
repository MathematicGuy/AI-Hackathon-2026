from pathlib import Path

import pytest

from backend.app.ingestion.catalog import (
    CATALOG_FILENAME,
    _jsonable,
    _text,
    iter_rows,
)

DATASET = Path("data/dataset") / CATALOG_FILENAME

needs_dataset = pytest.mark.skipif(
    not DATASET.exists(), reason="catalog dataset not present"
)


def test_text_normalization():
    assert _text("  x ") == "x"
    assert _text("   ") is None
    assert _text(None) is None
    assert _text(362465) == "362465"


def test_jsonable_strips_and_blanks_to_none():
    assert _jsonable("  a ") == "a"
    assert _jsonable("") is None
    assert _jsonable(29490000) == 29490000
    assert _jsonable(None) is None


@needs_dataset
def test_all_sheets_present_and_sku_is_unique_key():
    rows = list(iter_rows(DATASET))
    assert len(rows) == 8746
    sheets = {sheet for sheet, _ in rows}
    assert len(sheets) == 14
    assert "Máy lạnh" in sheets

    skus = [_text(record.get("sku")) for _, record in rows]
    assert all(sku is not None for sku in skus), "every row must have a sku"
    assert len(skus) == len(set(skus)), "sku must be unique across all sheets"


@needs_dataset
def test_maylanh_rows_preserve_original_headers_verbatim():
    rows = [record for sheet, record in iter_rows(DATASET) if sheet == "Máy lạnh"]
    assert len(rows) == 1039
    sample = rows[0]
    for original_header in (
        "model_code",
        "sku",
        "productidweb",
        "category_code",
        "brand",
        "giá gốc",
        "Phạm vi sử dụng",
        "khuyến mãi quà",
    ):
        assert original_header in sample, f"missing original column {original_header!r}"
