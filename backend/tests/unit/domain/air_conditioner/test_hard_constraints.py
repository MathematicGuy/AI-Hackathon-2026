"""US-108 deterministic hard-constraint filtering."""

import json
from pathlib import Path

import pytest

from backend.app.contracts.schemas import AirConditionerNeed, NeedPriority
from backend.app.domain.air_conditioner.evidence import NormalizedProduct
from backend.app.domain.air_conditioner.hard_constraints import filter_products
from backend.app.domain.air_conditioner.normalization import normalize_catalog


CATALOG_PATH = Path("data/aircon-m1-test-data/aircon-m1-catalog-enriched.json")


@pytest.fixture(scope="module")
def normalized_products():
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return normalize_catalog(catalog)


def _need(*priorities, budget=20_000_000, room=18):
    return AirConditionerNeed(
        budget_max_vnd=budget,
        room_size_m2=room,
        priorities=[
            NeedPriority(name=name, importance=importance)
            for name, importance in priorities
        ],
    )


def _variant(normalized_products, **updates):
    base = normalized_products[0]
    missing = tuple(updates.pop("_missing_fields", ()))
    product = base.product.model_copy(update=updates)
    evidence = dict(base.evidence)
    for field in missing:
        evidence.pop(field, None)
    return NormalizedProduct(product=product, evidence=evidence, missing_fields=missing)


def _ids(products):
    return [product.product_id for product in products]


def test_golden_aircon_001_split_is_ordered_and_grounded(normalized_products):
    result = filter_products(
        normalized_products,
        _need(("energy_saving", "primary"), ("low_noise", "secondary")),
    )

    assert _ids(result.eligible_products) == [
        f"AC-M1-{number:03d}" for number in range(1, 9)
    ]
    assert [item.product_id for item in result.excluded_products] == [
        f"AC-M1-{number:03d}" for number in range(9, 15)
    ]
    reasons = {
        item.product_id: item.reasons for item in result.excluded_products
    }
    assert any("missing required evidence 'cspf'" in reason for reason in reasons["AC-M1-009"])
    assert any("room_size_m2" in reason for reason in reasons["AC-M1-010"])
    assert any("stock_status is unavailable" in reason for reason in reasons["AC-M1-012"])
    assert any("stock_status unknown" in reason for reason in reasons["AC-M1-014"])
    assert any("exceeds budget_max_vnd" in reason for reason in reasons["AC-M1-014"])

    by_id = {item.product.product_id: item for item in normalized_products}
    assert "stock_status" in by_id["AC-M1-012"].evidence
    assert "stock_status" in by_id["AC-M1-014"].evidence
    assert "cspf" in by_id["AC-M1-009"].missing_fields
    assert "cspf" not in by_id["AC-M1-009"].evidence


def test_filter_is_deterministic(normalized_products):
    need = _need(("energy_saving", "primary"), ("low_noise", "secondary"))
    assert filter_products(normalized_products, need) == filter_products(
        normalized_products, need
    )


@pytest.mark.parametrize(
    ("price", "expected_excluded"),
    [(20_000_001, True), (20_000_000, False), (19_999_999, False), (None, False)],
)
def test_budget_constraint(normalized_products, price, expected_excluded):
    product = _variant(normalized_products, sale_price_vnd=price)
    result = filter_products([product], _need())
    assert bool(result.excluded_products) is expected_excluded


@pytest.mark.parametrize(
    ("room", "minimum", "maximum", "expected_excluded"),
    [
        (9, 10, 20, True),
        (10, 10, 20, False),
        (20, 10, 20, False),
        (21, 10, 20, True),
        (18, None, 20, False),
        (18, 10, None, False),
        (9, None, 20, False),
        (21, 10, None, False),
    ],
)
def test_room_fit_uses_known_bounds_independently(
    normalized_products, room, minimum, maximum, expected_excluded
):
    product = _variant(
        normalized_products,
        recommended_room_area_min_m2=minimum,
        recommended_room_area_max_m2=maximum,
    )
    result = filter_products([product], _need(room=room))
    assert bool(result.excluded_products) is expected_excluded


@pytest.mark.parametrize(
    ("stock_status", "missing_fields", "expected_excluded"),
    [("available", (), False), ("unavailable", (), True), ("unknown", (), True), ("unknown", ("stock_status",), True)],
)
def test_available_only_stock_policy(
    normalized_products, stock_status, missing_fields, expected_excluded
):
    product = _variant(
        normalized_products,
        stock_status=stock_status,
        _missing_fields=missing_fields,
    )
    result = filter_products([product], _need())
    assert bool(result.excluded_products) is expected_excluded


def test_primary_evidence_is_required_but_secondary_evidence_is_not(normalized_products):
    missing_cspf = _variant(
        normalized_products, cspf=None, _missing_fields=("cspf",)
    )
    missing_noise = _variant(
        normalized_products,
        indoor_noise_min_db=None,
        _missing_fields=("indoor_noise_min_db",),
    )

    assert filter_products(
        [missing_cspf], _need(("energy_saving", "primary"))
    ).excluded_products
    assert filter_products(
        [missing_noise], _need(("low_noise", "primary"))
    ).excluded_products
    assert filter_products(
        [missing_noise], _need(("low_noise", "secondary"))
    ).eligible_products


def test_multiple_violations_accumulate_in_constraint_order(normalized_products):
    product = _variant(
        normalized_products,
        sale_price_vnd=21_000_000,
        recommended_room_area_min_m2=20,
        recommended_room_area_max_m2=30,
    )
    result = filter_products([product], _need())
    reasons = result.excluded_products[0].reasons
    assert len(reasons) == 2
    assert "exceeds budget_max_vnd" in reasons[0]
    assert "below recommended_room_area_min_m2" in reasons[1]
