import importlib
import json
import tempfile
from pathlib import Path

import pytest


SNAPSHOT = "synthetic-aircon-m1-2026-07-17"
MISSING = object()


class StaticAdapter:
    def __init__(self, records):
        self.records = records

    def load(self):
        return self.records


class MissingModule:
    def __init__(self, name):
        self.name = name

    def __getattr__(self, _attribute):
        pytest.fail(f"US-106 {self.name} module is not implemented")


@pytest.fixture
def product_search_module():
    try:
        return importlib.import_module("backend.app.tools.product_search")
    except ModuleNotFoundError:
        return MissingModule("product search")


@pytest.fixture
def catalog_adapter_module():
    try:
        return importlib.import_module("backend.app.tools.catalog_adapter")
    except ModuleNotFoundError:
        return MissingModule("catalog adapter")


def product(
    number,
    *,
    region_code="HCM",
    category="air_conditioner",
    source_snapshot=SNAPSHOT,
):
    record = {
        "product_id": f"AC-M1-{number:03d}",
        "category": category,
        "region_code": region_code,
        "input_position": number,
    }
    if source_snapshot is not MISSING:
        record["source_snapshot"] = source_snapshot
    return record


def ids(result):
    return [record["product_id"] for record in result.products]


def test_filters_default_to_air_conditioners_without_a_region(product_search_module):
    filters = product_search_module.AirConditionerFilters()

    assert filters.category == "air_conditioner"
    assert filters.region_code is None


def test_filters_reject_a_different_category(product_search_module):
    with pytest.raises(ValueError, match="air_conditioner"):
        product_search_module.AirConditionerFilters(category="television")


def test_default_limit_returns_three_products(product_search_module):
    records = [product(number) for number in range(1, 6)]

    result = product_search_module.search_air_conditioners(
        product_search_module.AirConditionerFilters(),
        adapter=StaticAdapter(records),
    )

    assert ids(result) == ["AC-M1-001", "AC-M1-002", "AC-M1-003"]
    assert result.next_cursor == 3
    assert result.total_candidates == 5
    assert result.has_more is True
    assert result.source_snapshot == SNAPSHOT


@pytest.mark.parametrize("limit", [1, 10])
def test_accepts_minimum_and_maximum_limits(product_search_module, limit):
    records = [product(number) for number in range(1, 12)]

    result = product_search_module.search_air_conditioners(
        product_search_module.AirConditionerFilters(),
        adapter=StaticAdapter(records),
        limit=limit,
    )

    assert len(result.products) == limit


@pytest.mark.parametrize("limit", [0, 11, -1, True, 1.5, "3", None])
def test_rejects_invalid_limits(product_search_module, limit):
    with pytest.raises(ValueError, match="invalid page request"):
        product_search_module.search_air_conditioners(
            product_search_module.AirConditionerFilters(),
            adapter=StaticAdapter([product(1)]),
            limit=limit,
        )


@pytest.mark.parametrize("cursor", [-1, True, 1.5, "1", None])
def test_rejects_negative_and_malformed_cursors(product_search_module, cursor):
    with pytest.raises(ValueError, match="invalid page request"):
        product_search_module.search_air_conditioners(
            product_search_module.AirConditionerFilters(),
            adapter=StaticAdapter([product(1)]),
            cursor=cursor,
        )


def test_pages_preserve_stable_catalog_order(product_search_module):
    records = [product(number) for number in range(1, 9)]
    filters = product_search_module.AirConditionerFilters()

    first = product_search_module.search_air_conditioners(
        filters, adapter=StaticAdapter(records), limit=4
    )
    second = product_search_module.search_air_conditioners(
        filters, adapter=StaticAdapter(records), limit=4, cursor=first.next_cursor
    )

    assert ids(first) == ["AC-M1-001", "AC-M1-002", "AC-M1-003", "AC-M1-004"]
    assert ids(second) == ["AC-M1-005", "AC-M1-006", "AC-M1-007", "AC-M1-008"]
    assert second.next_cursor is None
    assert second.has_more is False


def test_cursor_and_exclusions_do_not_skip_candidates(product_search_module):
    records = [product(number) for number in range(1, 8)]
    filters = product_search_module.AirConditionerFilters(region_code="HCM")

    first = product_search_module.search_air_conditioners(
        filters,
        adapter=StaticAdapter(records),
        limit=3,
        exclude_product_ids=["AC-M1-002"],
    )
    second = product_search_module.search_air_conditioners(
        filters,
        adapter=StaticAdapter(records),
        limit=3,
        cursor=first.next_cursor,
        exclude_product_ids=ids(first),
    )

    assert ids(first) == ["AC-M1-001", "AC-M1-003", "AC-M1-004"]
    assert first.next_cursor == 4
    assert ids(second) == ["AC-M1-005", "AC-M1-006", "AC-M1-007"]
    assert set(ids(first)).isdisjoint(ids(second))


def test_total_candidates_is_counted_before_exclusions(product_search_module):
    records = [product(number) for number in range(1, 6)]

    result = product_search_module.search_air_conditioners(
        product_search_module.AirConditionerFilters(),
        adapter=StaticAdapter(records),
        exclude_product_ids=["AC-M1-001", "AC-M1-003"],
        limit=10,
    )

    assert ids(result) == ["AC-M1-002", "AC-M1-004", "AC-M1-005"]
    assert result.total_candidates == 5


def test_out_of_range_cursor_returns_a_terminal_empty_page(product_search_module):
    records = [product(number) for number in range(1, 4)]

    result = product_search_module.search_air_conditioners(
        product_search_module.AirConditionerFilters(),
        adapter=StaticAdapter(records),
        cursor=99,
    )

    assert result.products == []
    assert result.next_cursor is None
    assert result.total_candidates == 3
    assert result.has_more is False
    assert result.source_snapshot == SNAPSHOT


def test_excluded_terminal_tail_returns_a_terminal_empty_page(product_search_module):
    records = [product(number) for number in range(1, 6)]

    result = product_search_module.search_air_conditioners(
        product_search_module.AirConditionerFilters(),
        adapter=StaticAdapter(records),
        cursor=3,
        exclude_product_ids=["AC-M1-004", "AC-M1-005"],
    )

    assert result.products == []
    assert result.next_cursor is None
    assert result.has_more is False


def test_full_page_with_only_excluded_records_remaining_is_terminal(
    product_search_module,
):
    records = [product(number) for number in range(1, 6)]

    result = product_search_module.search_air_conditioners(
        product_search_module.AirConditionerFilters(),
        adapter=StaticAdapter(records),
        limit=3,
        exclude_product_ids=["AC-M1-004", "AC-M1-005"],
    )

    assert ids(result) == ["AC-M1-001", "AC-M1-002", "AC-M1-003"]
    assert result.next_cursor is None
    assert result.has_more is False


def test_region_filter_is_optional_exact_and_stable(product_search_module):
    records = [
        product(1, region_code="HN"),
        product(2, region_code="HCM"),
        product(3, region_code="hcm"),
        product(4, region_code="HCM"),
    ]

    result = product_search_module.search_air_conditioners(
        product_search_module.AirConditionerFilters(region_code="HCM"),
        adapter=StaticAdapter(records),
        limit=10,
    )

    assert ids(result) == ["AC-M1-002", "AC-M1-004"]
    assert result.total_candidates == 2


def test_non_air_conditioners_are_not_candidates(product_search_module):
    records = [product(1), product(2, category="television"), product(3)]

    result = product_search_module.search_air_conditioners(
        product_search_module.AirConditionerFilters(),
        adapter=StaticAdapter(records),
        limit=10,
    )

    assert ids(result) == ["AC-M1-001", "AC-M1-003"]
    assert result.total_candidates == 2


def test_search_returns_records_without_normalizing_or_ranking(product_search_module):
    records = [product(2), product(1)]

    result = product_search_module.search_air_conditioners(
        product_search_module.AirConditionerFilters(),
        adapter=StaticAdapter(records),
        limit=10,
    )

    assert result.products == records


@pytest.mark.parametrize(
    "records",
    [
        [product(1), product(2, source_snapshot="another-snapshot")],
        [product(1), product(2, source_snapshot=MISSING)],
    ],
)
def test_rejects_mixed_or_missing_source_snapshots(product_search_module, records):
    with pytest.raises(ValueError, match="source_snapshot"):
        product_search_module.search_air_conditioners(
            product_search_module.AirConditionerFilters(),
            adapter=StaticAdapter(records),
        )


def test_snapshot_validation_ignores_unrelated_candidates(product_search_module):
    records = [
        product(1, region_code="HCM", source_snapshot=SNAPSHOT),
        product(2, region_code="HN", source_snapshot="another-snapshot"),
        product(3, category="television", source_snapshot=MISSING),
    ]

    result = product_search_module.search_air_conditioners(
        product_search_module.AirConditionerFilters(region_code="HCM"),
        adapter=StaticAdapter(records),
    )

    assert ids(result) == ["AC-M1-001"]
    assert result.source_snapshot == SNAPSHOT


def test_zero_candidates_use_the_uniform_catalog_snapshot(product_search_module):
    records = [product(1, region_code="HN"), product(2, category="television")]

    result = product_search_module.search_air_conditioners(
        product_search_module.AirConditionerFilters(region_code="HCM"),
        adapter=StaticAdapter(records),
    )

    assert result.products == []
    assert result.source_snapshot == SNAPSHOT


def test_zero_candidates_reject_mixed_catalog_snapshots(product_search_module):
    records = [
        product(1, region_code="HN", source_snapshot=SNAPSHOT),
        product(2, category="television", source_snapshot="another-snapshot"),
    ]

    with pytest.raises(ValueError, match="source_snapshot"):
        product_search_module.search_air_conditioners(
            product_search_module.AirConditionerFilters(region_code="HCM"),
            adapter=StaticAdapter(records),
        )


@pytest.mark.parametrize("source_snapshot", [None, "", 42, [SNAPSHOT]])
def test_rejects_malformed_source_snapshots(
    product_search_module, source_snapshot
):
    with pytest.raises(ValueError, match="source_snapshot"):
        product_search_module.search_air_conditioners(
            product_search_module.AirConditionerFilters(),
            adapter=StaticAdapter([product(1, source_snapshot=source_snapshot)]),
        )


@pytest.mark.parametrize("product_id", [MISSING, None, "", 42])
def test_rejects_missing_non_string_or_empty_product_ids(
    product_search_module, product_id
):
    record = product(1)
    if product_id is MISSING:
        del record["product_id"]
    else:
        record["product_id"] = product_id

    with pytest.raises(ValueError, match="product_id"):
        product_search_module.search_air_conditioners(
            product_search_module.AirConditionerFilters(),
            adapter=StaticAdapter([record]),
        )


@pytest.mark.parametrize("records", [{"products": []}, "not-a-list", None])
def test_search_rejects_non_list_catalogs(product_search_module, records):
    with pytest.raises(ValueError, match="catalog must be a list"):
        product_search_module.search_air_conditioners(
            product_search_module.AirConditionerFilters(),
            adapter=StaticAdapter(records),
        )


def test_search_rejects_non_object_catalog_records(product_search_module):
    with pytest.raises(ValueError, match="catalog records must be objects"):
        product_search_module.search_air_conditioners(
            product_search_module.AirConditionerFilters(),
            adapter=StaticAdapter([product(1), "bad-record"]),
        )


def test_catalog_adapter_loads_a_json_list_without_reordering(catalog_adapter_module):
    records = [product(2), product(1)]
    with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
        catalog_path = Path(directory) / "catalog.json"
        catalog_path.write_text(json.dumps(records), encoding="utf-8")

        loaded = catalog_adapter_module.CatalogAdapter(catalog_path).load()

    assert loaded == records


def test_catalog_adapter_rejects_a_non_list_json_document(catalog_adapter_module):
    with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
        catalog_path = Path(directory) / "catalog.json"
        catalog_path.write_text(json.dumps({"products": []}), encoding="utf-8")

        with pytest.raises(ValueError, match="catalog must be a list"):
            catalog_adapter_module.CatalogAdapter(catalog_path).load()
