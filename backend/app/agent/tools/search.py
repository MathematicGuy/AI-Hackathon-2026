"""Deterministic product search with budget/brand/keyword/attribute filters.

Sort order is stable and price-ascending on the effective (promotion) price;
products without a parsable price sort last and are excluded entirely when a
budget constraint is active — the agent never guesses a price into a budget.
"""

from dataclasses import dataclass, field

from backend.app.agent.catalog.dataset_adapter import GenericProduct


@dataclass(frozen=True, slots=True)
class SearchResult:
    items: list[GenericProduct]
    next_cursor: int | None
    total_candidates: int
    has_more: bool
    applied_filters: dict = field(default_factory=dict)


def _matches(product: GenericProduct, *, budget_min, budget_max, brands,
             keywords, attribute_contains) -> bool:
    price = product.effective_price
    if budget_min is not None or budget_max is not None:
        if price is None:
            return False
        if budget_min is not None and price < budget_min:
            return False
        if budget_max is not None and price > budget_max:
            return False
    if brands:
        brand = (product.brand or "").lower()
        if brand not in {b.lower() for b in brands}:
            return False
    if keywords:
        haystack = " ".join(
            str(value).lower()
            for value in product.attributes.values()
            if value is not None
        )
        if not all(keyword.lower() in haystack for keyword in keywords):
            return False
    for key, fragment in (attribute_contains or {}).items():
        value = product.attributes.get(key)
        if value is None or fragment.lower() not in str(value).lower():
            return False
    return True


def search_products(
    products: list[GenericProduct],
    *,
    category_code: str,
    budget_min: int | None = None,
    budget_max: int | None = None,
    brands: tuple[str, ...] = (),
    keywords: tuple[str, ...] = (),
    attribute_contains: dict[str, str] | None = None,
    limit: int = 5,
    cursor: int = 0,
    exclude_ids: tuple[str, ...] = (),
) -> SearchResult:
    if not (isinstance(limit, int) and 1 <= limit <= 20) or cursor < 0:
        raise ValueError("invalid page request")

    candidates = [
        product
        for product in products
        if product.category_code == str(category_code)
        and _matches(
            product,
            budget_min=budget_min,
            budget_max=budget_max,
            brands=brands,
            keywords=keywords,
            attribute_contains=attribute_contains,
        )
    ]
    candidates.sort(
        key=lambda p: (
            p.effective_price is None,
            p.effective_price if p.effective_price is not None else 0,
            p.productidweb,
        )
    )

    excluded = set(exclude_ids)
    page: list[GenericProduct] = []
    scan = min(cursor, len(candidates))
    while scan < len(candidates) and len(page) < limit:
        candidate = candidates[scan]
        scan += 1
        if candidate.productidweb not in excluded:
            page.append(candidate)

    has_more = any(
        candidate.productidweb not in excluded for candidate in candidates[scan:]
    )
    return SearchResult(
        items=page,
        next_cursor=scan if has_more else None,
        total_candidates=len(candidates),
        has_more=has_more,
        applied_filters={
            "category_code": str(category_code),
            "budget_min": budget_min,
            "budget_max": budget_max,
            "brands": list(brands),
            "keywords": list(keywords),
            "attribute_contains": dict(attribute_contains or {}),
        },
    )
