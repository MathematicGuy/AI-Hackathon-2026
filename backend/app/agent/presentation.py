"""Render-ready presentation mapping over the records used by the E02 reply."""

from collections.abc import Iterable

from backend.app.agent.catalog.dataset_adapter import GenericProduct
from backend.app.agent.contracts import (
    AgentPresentation,
    ComparisonRow,
    ComparisonValue,
    PresentationBadge,
    PresentationHighlight,
    PresentedProduct,
)
from backend.app.agent.respond import ROLE_LABELS, format_vnd
from backend.app.agent.tools.compare import Comparison
from backend.app.agent.tools.suggest import Suggestions

_NON_HIGHLIGHT_ATTRIBUTES = {
    "model_code",
    "sku",
    "productidweb",
    "category_code",
    "brand_id",
    "brand",
    "giá gốc",
    "giá khuyến mãi",
    "khuyến mãi quà",
}
_SKU_WARNING = "Không thể hiển thị sản phẩm vì SKU ổn định đang thiếu hoặc bị trùng."
_DMX_PRODUCT_URL_PREFIX = "https://www.dienmayxanh.com/p/"


def _bounded_text(value: object, max_length: int) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if len(text) <= max_length:
        return text
    return text[: max_length - 1].rstrip() + "…"


def _bounded_fact(value: object, max_length: int) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or len(text) > max_length:
        return None
    return text


def _sku(product: GenericProduct) -> str | None:
    if product.sku is None:
        return None
    value = str(product.sku).strip()
    return value if value and len(value) <= 128 else None


def _source_productidweb(product: GenericProduct) -> str | None:
    return _bounded_fact(product.attributes.get("productidweb"), 128)


def _dedupe_same_records(products: Iterable[GenericProduct]) -> list[GenericProduct]:
    result: list[GenericProduct] = []
    seen: set[tuple[str | None, str]] = set()
    for product in products:
        key = (_sku(product), product.productidweb)
        if key in seen:
            continue
        seen.add(key)
        result.append(product)
    return result


def _has_unique_skus(products: list[GenericProduct]) -> bool:
    skus = [_sku(product) for product in products]
    return bool(skus) and None not in skus and len(skus) == len(set(skus))


def _highlights(product: GenericProduct) -> list[PresentationHighlight]:
    highlights: list[PresentationHighlight] = []
    for label, raw_value in product.attributes.items():
        clean_label = str(label).strip()
        if not clean_label or clean_label.casefold() in _NON_HIGHLIGHT_ATTRIBUTES:
            continue
        if raw_value in (None, ""):
            continue
        bounded_label = _bounded_text(clean_label, 120)
        value = _bounded_fact(raw_value, 500)
        if bounded_label is None or value is None:
            continue
        highlights.append(PresentationHighlight(label=bounded_label, value=value))
        if len(highlights) == 3:
            break
    return highlights


def _is_presentable_attribute(label: object) -> bool:
    clean = str(label).strip()
    return bool(clean) and clean.casefold() not in _NON_HIGHLIGHT_ATTRIBUTES


def _attribute_value(product: GenericProduct, label: str) -> object | None:
    for raw_label, value in product.attributes.items():
        if str(raw_label).strip() == label:
            return value
    return None


def _comparison_attribute_labels(
    products: list[GenericProduct], comparison: Comparison
) -> list[str]:
    labels = [
        str(label).strip()
        for label in comparison.shared_attributes
        if _is_presentable_attribute(label)
    ]
    candidates = {
        str(label).strip()
        for product in products
        for label, value in product.attributes.items()
        if _is_presentable_attribute(label) and value not in (None, "")
    }
    for label in sorted(candidates, key=str.casefold):
        if label not in labels:
            labels.append(label)
    return labels[:3]


def _product_url(product: GenericProduct) -> str | None:
    """Construct the canonical DMX product URL from productidweb when valid."""
    pid = product.productidweb
    if not pid or not isinstance(pid, str):
        return None
    pid = pid.strip()
    if not pid or len(pid) > 128:
        return None
    return _DMX_PRODUCT_URL_PREFIX + pid


def _present_product(
    product: GenericProduct,
    *,
    badge_codes: Iterable[str] = (),
) -> PresentedProduct:
    sku = _sku(product)
    if sku is None:
        raise ValueError("presented product requires a stable SKU")
    return PresentedProduct(
        sku=sku,
        # GenericProduct.productidweb may contain a SKU fallback. Only expose
        # the raw mirror attribute when the source preserved it explicitly.
        productidweb=_source_productidweb(product),
        name=_bounded_fact(product.name, 300) or sku,
        brand=_bounded_fact(product.brand, 120),
        effective_price_vnd=product.effective_price,
        list_price_vnd=product.list_price,
        discount_percent=product.promotion.discount_percent,
        promotion_text=_bounded_fact(product.gift_promotion, 500),
        badges=_badges(badge_codes),
        highlights=_highlights(product),
        image_url=None,
        product_url=_product_url(product),
        rating=None,
        sold_count=None,
    )


def _follow_ups(question: str | None) -> list[str]:
    if question is None:
        return []
    clean = _bounded_text(question, 500)
    return [clean] if clean else []


def _badges(badge_codes: Iterable[str]) -> list[PresentationBadge]:
    badges: list[PresentationBadge] = []
    seen: set[str] = set()
    for raw_code in badge_codes:
        code = str(raw_code).strip()
        if not code or len(code) > 64 or code in seen:
            continue
        label = _bounded_text(ROLE_LABELS.get(code, code), 120)
        if label is None:
            continue
        badges.append(PresentationBadge(code=code, label=label))
        seen.add(code)
        if len(badges) == 10:
            break
    return badges


def _role_warnings(skipped_roles: Iterable[str]) -> list[str]:
    warnings: list[str] = []
    seen: set[str] = set()
    for raw_role in skipped_roles:
        role = str(raw_role).strip()
        label = ROLE_LABELS.get(role, role)
        warning = _bounded_text("Chưa đủ dữ liệu cho vai trò: " + label, 500)
        if warning is None or warning in seen:
            continue
        warnings.append(warning)
        seen.add(warning)
        if len(warnings) == 10:
            break
    return warnings


def build_recommendation_presentation(
    suggestions: Suggestions,
    *,
    also_consider: list[GenericProduct] | None = None,
    follow_up_question: str | None = None,
) -> AgentPresentation:
    products = _dedupe_same_records(
        [*suggestions.distinct_products, *(also_consider or [])]
    )
    warnings = _role_warnings(suggestions.skipped_roles)
    if not _has_unique_skus(products):
        return AgentPresentation(
            type="text", warnings=[*warnings[:9], _SKU_WARNING]
        )

    presented: list[PresentedProduct] = []
    for product in products:
        product_sku = _sku(product)
        badge_codes = [
            role
            for role, winner in suggestions.winners.items()
            if _sku(winner) == product_sku
        ]
        presented.append(_present_product(product, badge_codes=badge_codes))
    return AgentPresentation(
        type="recommendation",
        products=presented,
        follow_up_questions=_follow_ups(follow_up_question),
        warnings=warnings,
    )


def _resolve_comparison_products(
    products: list[GenericProduct], comparison: Comparison
) -> list[GenericProduct] | None:
    resolved: list[GenericProduct] = []
    for item in comparison.items:
        matches = [
            product
            for product in products
            if product.productidweb == item.productidweb
        ]
        if len(matches) != 1:
            return None
        resolved.append(matches[0])
    return resolved


def _comparison_row(
    label: str,
    products: list[GenericProduct],
    values: Iterable[str | None],
) -> ComparisonRow:
    return ComparisonRow(
        label=_bounded_text(label, 120) or "Thông tin",
        values=[
            ComparisonValue(
                sku=_sku(product) or "",
                value=_bounded_fact(value, 500),
            )
            for product, value in zip(products, values, strict=True)
        ],
    )


def build_comparison_presentation(
    products: list[GenericProduct],
    comparison: Comparison,
    *,
    follow_up_question: str | None = None,
) -> AgentPresentation:
    selected = _resolve_comparison_products(products, comparison)
    if selected is None or len(selected) < 2 or not _has_unique_skus(selected):
        return AgentPresentation(type="text", warnings=[_SKU_WARNING])

    rows = [
        _comparison_row(
            "Giá hiện tại",
            selected,
            (
                format_vnd(item.effective_price)
                if item.effective_price is not None
                else None
                for item in comparison.items
            ),
        ),
        _comparison_row(
            "Giá niêm yết",
            selected,
            (
                format_vnd(item.list_price)
                if item.list_price is not None
                else None
                for item in comparison.items
            ),
        ),
        _comparison_row(
            "Giảm giá",
            selected,
            (
                f"{item.discount_percent:.0f}%"
                if item.discount_percent is not None
                else None
                for item in comparison.items
            ),
        ),
        _comparison_row(
            "Khuyến mãi",
            selected,
            (item.gift for item in comparison.items),
        ),
    ]
    for label in _comparison_attribute_labels(selected, comparison):
        values_by_id = comparison.shared_attributes.get(label)
        rows.append(
            _comparison_row(
                label,
                selected,
                (
                    values_by_id.get(product.productidweb)
                    if values_by_id is not None
                    else _attribute_value(product, label)
                    for product in selected
                ),
            )
        )

    return AgentPresentation(
        type="comparison",
        products=[_present_product(product) for product in selected],
        comparison_rows=rows,
        follow_up_questions=_follow_ups(follow_up_question),
    )
