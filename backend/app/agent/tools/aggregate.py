"""Category-level aggregation: brands, price range, promotion coverage."""

from collections import Counter
from dataclasses import dataclass

from backend.app.agent.catalog.dataset_adapter import GenericProduct


@dataclass(frozen=True, slots=True)
class CategoryOverview:
    category_code: str
    product_count: int
    brand_counts: dict[str, int]
    price_min: int | None
    price_max: int | None
    discounted_count: int
    gift_count: int


def category_overview(
    products: list[GenericProduct], *, category_code: str
) -> CategoryOverview:
    members = [p for p in products if p.category_code == str(category_code)]
    prices = [p.effective_price for p in members if p.effective_price is not None]
    brands = Counter(p.brand for p in members if p.brand)
    return CategoryOverview(
        category_code=str(category_code),
        product_count=len(members),
        brand_counts=dict(brands),
        price_min=min(prices) if prices else None,
        price_max=max(prices) if prices else None,
        discounted_count=sum(
            1 for p in members if p.promotion.discount_percent is not None
        ),
        gift_count=sum(1 for p in members if p.gift_promotion),
    )


def attribute_values(
    products: list[GenericProduct], *, category_code: str, key: str, top: int = 10
) -> list[tuple[str, int]]:
    values = Counter(
        str(p.attributes[key]).strip()
        for p in products
        if p.category_code == str(category_code)
        and p.attributes.get(key) not in (None, "")
    )
    return values.most_common(top)
