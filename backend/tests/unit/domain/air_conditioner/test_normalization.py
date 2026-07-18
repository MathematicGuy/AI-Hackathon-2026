"""US-107 deterministic product normalization and evidence."""

import copy
import json
from pathlib import Path

import pytest

from backend.app.contracts.schemas import EvidenceRef, NormalizedAirConditioner
from backend.app.domain.air_conditioner.evidence import NormalizedProduct
from backend.app.domain.air_conditioner.normalization import (
    normalize_air_conditioner,
    normalize_catalog,
)


CATALOG_PATH = Path("data/aircon-m1-test-data/aircon-m1-catalog-enriched.json")
SNAPSHOT = "synthetic-aircon-m1-2026-07-17"

# Fields parsed out of the labeled Vietnamese technical specifications.
PARSED_FIELDS = (
    "horsepower_hp",
    "cooling_capacity_btu",
    "recommended_room_area_min_m2",
    "recommended_room_area_max_m2",
    "cspf",
    "energy_label_stars",
    "rated_power_w",
    "annual_energy_kwh",
    "indoor_noise_min_db",
    "indoor_noise_max_db",
    "warranty_months",
    "installation_cost_vnd",
    "inverter",
)


@pytest.fixture(scope="module")
def catalog():
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def by_id(catalog):
    return {record["product_id"]: record for record in catalog}


def test_every_record_matches_golden_fixture(catalog):
    for record in catalog:
        result = normalize_air_conditioner(record)
        expected = NormalizedAirConditioner(**record["normalized_fixture"])
        assert result.product == expected, record["product_id"]


def test_result_is_normalized_product_with_contract_shape(catalog):
    result = normalize_air_conditioner(catalog[0])
    assert isinstance(result, NormalizedProduct)
    assert isinstance(result.product, NormalizedAirConditioner)


def test_evidence_present_for_every_populated_field(catalog):
    result = normalize_air_conditioner(catalog[0])
    populated = {
        name
        for name, value in result.product.model_dump().items()
        if value not in (None, {}, "")
    }
    for name in populated:
        assert name in result.evidence, name
        ref = result.evidence[name]
        assert isinstance(ref, EvidenceRef)
        assert ref.source_snapshot == SNAPSHOT
        assert ref.path.startswith("$")


def test_promotion_text_is_derived_from_discount_with_discount_evidence(catalog):
    record = catalog[0]
    result = normalize_air_conditioner(record)
    discount = record["discount_percent"]
    assert result.product.promotion_text == (
        f"Giảm {discount}% trong dữ liệu tổng hợp"
    )
    assert result.evidence["promotion_text"].path == "$.discount_percent"


def test_parsed_numeric_fields_have_spec_evidence_paths(catalog):
    result = normalize_air_conditioner(catalog[0])
    for name in PARSED_FIELDS:
        if result.product.__getattribute__(name) is None:
            continue
        assert result.evidence[name].path.startswith(
            "$.technical_specifications.sections["
        )


def test_missing_energy_fields_preserved_as_null_and_disclosed(by_id):
    result = normalize_air_conditioner(by_id["AC-M1-009"])
    assert result.product.cspf is None
    assert result.product.energy_label_stars is None
    assert result.product.annual_energy_kwh is None
    for name in ("cspf", "energy_label_stars", "annual_energy_kwh"):
        assert name in result.missing_fields
        assert name not in result.evidence


def test_missing_noise_fields_preserved_as_null(by_id):
    result = normalize_air_conditioner(by_id["AC-M1-008"])
    assert result.product.indoor_noise_min_db is None
    assert result.product.indoor_noise_max_db is None
    assert "indoor_noise_min_db" in result.missing_fields
    assert "indoor_noise_max_db" in result.missing_fields


def test_room_area_range_is_split(by_id):
    result = normalize_air_conditioner(by_id["AC-M1-010"])
    assert result.product.recommended_room_area_min_m2 == 10
    assert result.product.recommended_room_area_max_m2 == 15


def test_malformed_btu_is_rejected(catalog):
    bad = copy.deepcopy(catalog[0])
    bad["technical_specifications"]["sections"][0]["attributes"][
        "Công suất làm lạnh"
    ] = "abc BTU"
    with pytest.raises(ValueError):
        normalize_air_conditioner(bad)


def test_wrong_category_is_rejected(catalog):
    bad = copy.deepcopy(catalog[0])
    bad["category"] = "refrigerator"
    with pytest.raises(ValueError):
        normalize_air_conditioner(bad)


def test_missing_source_snapshot_is_rejected(catalog):
    bad = copy.deepcopy(catalog[0])
    del bad["source_snapshot"]
    with pytest.raises(ValueError):
        normalize_air_conditioner(bad)


def test_missing_product_id_is_rejected(catalog):
    bad = copy.deepcopy(catalog[0])
    del bad["product_id"]
    with pytest.raises(ValueError):
        normalize_air_conditioner(bad)


def test_normalize_catalog_returns_one_result_per_record(catalog):
    results = normalize_catalog(catalog)
    assert len(results) == len(catalog)
    assert all(isinstance(result, NormalizedProduct) for result in results)


def test_normalize_catalog_rejects_mixed_snapshot(catalog):
    mixed = [copy.deepcopy(catalog[0]), copy.deepcopy(catalog[1])]
    mixed[1]["source_snapshot"] = "other-snapshot"
    with pytest.raises(ValueError):
        normalize_catalog(mixed)
