"""Deterministic normalization of raw máy lạnh catalog records (US-107).

Turns one raw catalog record into a contract-frozen `NormalizedAirConditioner`
plus a per-field evidence map. Missing source values are preserved as `null`
and disclosed; malformed values are rejected, never guessed.
"""

import re
from typing import Any

from backend.app.contracts.schemas import EvidenceRef, NormalizedAirConditioner

from .evidence import NormalizedProduct, make_evidence


CATEGORY = "air_conditioner"

# technical_specifications.sections are ordered; every M1 record shares this shape.
_SEC_OVERVIEW = 0
_SEC_ENERGY = 1
_SEC_NOISE = 2
_SEC_WARRANTY = 3

# Labeled Vietnamese attributes inside each section.
_HP = "Công suất HP"
_BTU = "Công suất làm lạnh"
_AREA = "Diện tích phù hợp"
_INVERTER = "Công nghệ Inverter"
_CSPF = "CSPF"
_STARS = "Nhãn năng lượng"
_RATED_W = "Công suất điện định mức"
_ANNUAL_KWH = "Điện năng tiêu thụ ước tính"
_NOISE_MIN = "Độ ồn dàn lạnh thấp nhất"
_NOISE_MAX = "Độ ồn dàn lạnh cao nhất"
_WARRANTY = "Bảo hành"
_INSTALL = "Chi phí lắp đặt tham khảo"

_REQUIRED_STRINGS = (
    "product_id",
    "external_key",
    "name",
    "brand",
    "source_url",
    "source_snapshot",
)


def _grouped_int(text: Any) -> int:
    """Parse an integer, dropping unit suffixes and `.`/`,` grouping."""
    digits = re.sub(r"[^\d]", "", str(text))
    if not digits:
        raise ValueError(f"cannot parse integer from {text!r}")
    return int(digits)


def _decimal(text: Any) -> float:
    """Parse a decimal number, dropping unit suffixes (`6.10`, `18 dB`)."""
    cleaned = re.sub(r"[^\d.]", "", str(text))
    if not cleaned or cleaned == ".":
        raise ValueError(f"cannot parse number from {text!r}")
    return float(cleaned)


def _area_range(text: Any) -> tuple[float, float]:
    """Parse a room-area range `"15 - 20 m²"` into `(min, max)`."""
    numbers = [
        float(token.replace(",", "."))
        for token in re.findall(r"\d+(?:[.,]\d+)?", str(text))
    ]
    if not numbers:
        raise ValueError(f"cannot parse room area from {text!r}")
    if len(numbers) == 1:
        return numbers[0], numbers[0]
    return numbers[0], numbers[1]


def _inverter(text: Any) -> bool:
    value = str(text).strip().lower()
    if value in ("có", "co", "true", "yes", "1"):
        return True
    if value in ("không", "khong", "false", "no", "0"):
        return False
    raise ValueError(f"cannot parse inverter from {text!r}")


def _attr(sections: list[dict], index: int, label: str) -> Any:
    if index >= len(sections):
        return None
    return (sections[index].get("attributes") or {}).get(label)


def normalize_air_conditioner(record: dict) -> NormalizedProduct:
    """Normalize one raw catalog record into a `NormalizedProduct`."""
    if not isinstance(record, dict):
        raise ValueError("record must be a dict")
    if record.get("category") != CATEGORY:
        raise ValueError("record category must be air_conditioner")
    for name in _REQUIRED_STRINGS:
        key = "url" if name == "source_url" else name
        value = record.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"record is missing required field {name}")

    snapshot = record["source_snapshot"]
    sections = (record.get("technical_specifications") or {}).get("sections") or []

    fields: dict[str, Any] = {}
    evidence: dict[str, EvidenceRef] = {}
    missing: list[str] = []

    def _spec_path(index: int) -> str:
        return f"$.technical_specifications.sections[{index}]"

    def direct(field_name: str, raw_value: Any, path: str) -> None:
        if raw_value is None:
            fields[field_name] = None
            missing.append(field_name)
            return
        fields[field_name] = raw_value
        evidence[field_name] = make_evidence(path, snapshot)

    def parsed(field_name: str, raw_value: Any, parser, path: str) -> None:
        if raw_value is None:
            fields[field_name] = None
            missing.append(field_name)
            return
        fields[field_name] = parser(raw_value)
        evidence[field_name] = make_evidence(path, snapshot)

    # Identity and source (required strings validated above).
    for field_name in ("product_id", "external_key", "name", "brand"):
        fields[field_name] = record[field_name]
        evidence[field_name] = make_evidence(f"$.{field_name}", snapshot)
    fields["source_url"] = record["url"]
    evidence["source_url"] = make_evidence("$.url", snapshot)
    fields["source_snapshot"] = snapshot
    evidence["source_snapshot"] = make_evidence("$.source_snapshot", snapshot)

    # Structured top-level fields.
    direct("model", record.get("model"), "$.model")
    direct("sale_price_vnd", record.get("sale_price"), "$.sale_price")
    direct("list_price_vnd", record.get("list_price"), "$.list_price")
    direct("discount_percent", record.get("discount_percent"), "$.discount_percent")
    direct("region_code", record.get("region_code"), "$.region_code")
    direct("rating", record.get("rating"), "$.rating")
    direct("sold_count", record.get("sold_count"), "$.sold_count")

    stock = record.get("stock_status")
    if isinstance(stock, str) and stock:
        fields["stock_status"] = stock
        evidence["stock_status"] = make_evidence("$.stock_status", snapshot)
    else:
        fields["stock_status"] = "unknown"
        missing.append("stock_status")

    # Parsed technical specifications.
    parsed("horsepower_hp", _attr(sections, _SEC_OVERVIEW, _HP), _decimal,
           _spec_path(_SEC_OVERVIEW))
    parsed("cooling_capacity_btu", _attr(sections, _SEC_OVERVIEW, _BTU),
           _grouped_int, _spec_path(_SEC_OVERVIEW))

    area_raw = _attr(sections, _SEC_OVERVIEW, _AREA)
    if area_raw is None:
        fields["recommended_room_area_min_m2"] = None
        fields["recommended_room_area_max_m2"] = None
        missing.extend(
            ["recommended_room_area_min_m2", "recommended_room_area_max_m2"]
        )
    else:
        area_min, area_max = _area_range(area_raw)
        fields["recommended_room_area_min_m2"] = area_min
        fields["recommended_room_area_max_m2"] = area_max
        area_path = _spec_path(_SEC_OVERVIEW)
        evidence["recommended_room_area_min_m2"] = make_evidence(area_path, snapshot)
        evidence["recommended_room_area_max_m2"] = make_evidence(area_path, snapshot)

    parsed("inverter", _attr(sections, _SEC_ENERGY, _INVERTER), _inverter,
           _spec_path(_SEC_ENERGY))
    parsed("cspf", _attr(sections, _SEC_ENERGY, _CSPF), _decimal,
           _spec_path(_SEC_ENERGY))
    parsed("energy_label_stars", _attr(sections, _SEC_ENERGY, _STARS),
           _grouped_int, _spec_path(_SEC_ENERGY))
    parsed("rated_power_w", _attr(sections, _SEC_ENERGY, _RATED_W), _decimal,
           _spec_path(_SEC_ENERGY))
    parsed("annual_energy_kwh", _attr(sections, _SEC_ENERGY, _ANNUAL_KWH),
           _grouped_int, _spec_path(_SEC_ENERGY))
    parsed("indoor_noise_min_db", _attr(sections, _SEC_NOISE, _NOISE_MIN),
           _decimal, _spec_path(_SEC_NOISE))
    parsed("indoor_noise_max_db", _attr(sections, _SEC_NOISE, _NOISE_MAX),
           _decimal, _spec_path(_SEC_NOISE))
    parsed("warranty_months", _attr(sections, _SEC_WARRANTY, _WARRANTY),
           _grouped_int, _spec_path(_SEC_WARRANTY))
    parsed("installation_cost_vnd", _attr(sections, _SEC_WARRANTY, _INSTALL),
           _grouped_int, _spec_path(_SEC_WARRANTY))

    # Derived promotion text: a fixed template over the factual discount.
    discount = record.get("discount_percent")
    if discount is None:
        fields["promotion_text"] = None
        missing.append("promotion_text")
    else:
        fields["promotion_text"] = f"Giảm {discount}% trong dữ liệu tổng hợp"
        evidence["promotion_text"] = make_evidence("$.discount_percent", snapshot)

    product = NormalizedAirConditioner(**fields)
    return NormalizedProduct(
        product=product,
        evidence=evidence,
        missing_fields=tuple(missing),
    )


def normalize_catalog(records: list[dict]) -> list[NormalizedProduct]:
    """Normalize a page of records sharing one `source_snapshot`."""
    snapshots = {record.get("source_snapshot") for record in records}
    if len(snapshots) > 1:
        raise ValueError("records must share one source_snapshot")
    return [normalize_air_conditioner(record) for record in records]
