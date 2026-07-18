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


@dataclass(frozen=True, slots=True)
class ComparisonRow:
    """One dimension of the comparison table, as the client renders it.

    `values` is keyed by `productidweb` and holds the verbatim display text
    from the record. `winner_id` is set only where the dimension is rankable
    and one side actually wins.
    """

    label: str
    unit: str
    explain: str
    values: dict[str, str]
    winner_id: str | None = None


@dataclass(frozen=True, slots=True)
class ComparisonView:
    """Presentation projection of a comparison the agent already computed.

    Carried alongside the reply text so the client renders the same evidence
    the text is built from, instead of owning its own product data.
    """

    products: list[ComparisonItem]
    rows: list[ComparisonRow]
    price_delta: int | None = None


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
