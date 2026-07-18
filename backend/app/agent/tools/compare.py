"""Promotion-forward product comparison.

The comparison always leads with prices, discount percentages, and gifts —
not just specs — because purchase value is the customer's deciding factor.
"""

from dataclasses import dataclass

from backend.app.agent.catalog.dataset_adapter import GenericProduct


@dataclass(frozen=True, slots=True)
class ComparisonItem:
    productidweb: str
    name: str
    brand: str | None
    list_price: int | None
    sale_price: int | None
    effective_price: int | None
    discount_percent: float | None
    gift: str | None


@dataclass(frozen=True, slots=True)
class Comparison:
    items: list[ComparisonItem]
    shared_attributes: dict[str, dict[str, str]]
    price_delta: int | None


def compare_products(
    products: list[GenericProduct], product_ids: tuple[str, ...]
) -> Comparison:
    by_id = {p.productidweb: p for p in products}
    selected = [by_id[pid] for pid in product_ids]  # KeyError on unknown id

    items = [
        ComparisonItem(
            productidweb=p.productidweb,
            name=p.name,
            brand=p.brand,
            list_price=p.list_price,
            sale_price=p.sale_price,
            effective_price=p.effective_price,
            discount_percent=p.promotion.discount_percent,
            gift=p.gift_promotion,
        )
        for p in selected
    ]

    mirror_keys = {"model_code", "sku", "productidweb", "category_code", "brand_id",
                   "brand", "giá gốc", "giá khuyến mãi", "khuyến mãi quà"}
    shared: dict[str, dict[str, str]] = {}
    if selected:
        common_keys = set(selected[0].attributes)
        for product in selected[1:]:
            common_keys &= set(product.attributes)
        for key in sorted(common_keys - mirror_keys):
            values = {
                p.productidweb: str(p.attributes[key]).strip()
                for p in selected
                if p.attributes.get(key) not in (None, "")
            }
            if len(values) == len(selected):
                shared[key] = values

    prices = [item.effective_price for item in items if item.effective_price is not None]
    price_delta = max(prices) - min(prices) if len(prices) >= 2 else None
    return Comparison(items=items, shared_attributes=shared, price_delta=price_delta)
