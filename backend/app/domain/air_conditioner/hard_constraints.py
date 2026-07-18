"""Deterministic hard-constraint filtering for normalized air conditioners."""

from backend.app.contracts.schemas import (
    AirConditionerNeed,
    ExcludedProduct,
    FilterResult,
)

from .evidence import NormalizedProduct


_REQUIRED_EVIDENCE_BY_PRIMARY = {
    "energy_saving": ("cspf",),
    "low_noise": ("indoor_noise_min_db",),
}
_AVAILABLE_STOCK = "available"


def _required_primary_fields(need: AirConditionerNeed) -> list[tuple[str, str]]:
    required: list[tuple[str, str]] = []
    for priority in need.priorities:
        if priority.importance != "primary":
            continue
        for field in _REQUIRED_EVIDENCE_BY_PRIMARY.get(priority.name, ()):
            pair = (priority.name, field)
            if pair not in required:
                required.append(pair)
    return required


def filter_products(
    products: list[NormalizedProduct],
    need: AirConditionerNeed,
) -> FilterResult:
    """Split normalized products into eligible and excluded results."""
    eligible = []
    excluded = []
    required_primary_fields = _required_primary_fields(need)

    for normalized in products:
        product = normalized.product
        reasons: list[str] = []

        if (
            need.budget_max_vnd is not None
            and product.sale_price_vnd is not None
            and product.sale_price_vnd > need.budget_max_vnd
        ):
            reasons.append(
                f"sale_price_vnd {product.sale_price_vnd} exceeds "
                f"budget_max_vnd {need.budget_max_vnd}"
            )

        if need.room_size_m2 is not None:
            if (
                product.recommended_room_area_min_m2 is not None
                and need.room_size_m2 < product.recommended_room_area_min_m2
            ):
                reasons.append(
                    f"room_size_m2 {need.room_size_m2} below "
                    "recommended_room_area_min_m2 "
                    f"{product.recommended_room_area_min_m2}"
                )
            if (
                product.recommended_room_area_max_m2 is not None
                and need.room_size_m2 > product.recommended_room_area_max_m2
            ):
                reasons.append(
                    f"room_size_m2 {need.room_size_m2} above "
                    "recommended_room_area_max_m2 "
                    f"{product.recommended_room_area_max_m2}"
                )

        if product.stock_status != _AVAILABLE_STOCK:
            if product.stock_status == "unavailable":
                reasons.append("stock_status is unavailable")
            else:
                reasons.append(
                    "stock_status unknown does not satisfy stock_policy available"
                )

        for priority, field in required_primary_fields:
            value = getattr(product, field)
            if value is None or field in normalized.missing_fields or field not in normalized.evidence:
                reasons.append(
                    f"missing required evidence '{field}' for primary priority "
                    f"'{priority}'"
                )

        if reasons:
            excluded.append(
                ExcludedProduct(product_id=product.product_id, reasons=reasons)
            )
        else:
            eligible.append(product)

    return FilterResult(
        eligible_products=eligible,
        excluded_products=excluded,
    )
