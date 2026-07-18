"""Per-category domain rules: turn captured answers into deterministic
filters. Semi-independent per category so each ngành can evolve on its own
(Cường's direction). A rule returns predicates over GenericProduct; products
failing a predicate are dropped from the suggestion pool. Rules only fire when
the data carries the needed attribute — they never guess.

NEEDS DOMAIN-EXPERT REVIEW — capacity bands are provisional retail heuristics.
"""

import re
from typing import Callable

from backend.app.agent.catalog.dataset_adapter import GenericProduct
from backend.app.agent.contracts import GenericNeed

Predicate = Callable[[GenericProduct], bool]

_NUMBER = re.compile(r"(\d+(?:[.,]\d+)?)")


def _first_number(text: object) -> float | None:
    if text in (None, ""):
        return None
    match = _NUMBER.search(str(text))
    return float(match.group(1).replace(",", ".")) if match else None


def _numbers(text: object) -> list[float]:
    if text in (None, ""):
        return []
    return [float(m.group(1).replace(",", ".")) for m in _NUMBER.finditer(str(text))]


def _household_size(need: GenericNeed) -> int | None:
    answer = need.attribute_constraints.get("household")
    value = _first_number(answer)
    return int(value) if value else None


def _fridge_rules(need: GenericNeed) -> list[Predicate]:
    """Tủ Lạnh: household size → capacity band on 'Dung tích sử dụng'.
    1–2 người ≤ 250L; 3–4 người 200–450L; 5+ người ≥ 350L."""
    size = _household_size(need)
    if size is None:
        return []
    if size <= 2:
        low, high = 0.0, 250.0
    elif size <= 4:
        low, high = 200.0, 450.0
    else:
        low, high = 350.0, 10_000.0

    def fits(product: GenericProduct) -> bool:
        capacity = _first_number(product.attributes.get("Dung tích sử dụng"))
        if capacity is None:
            return True  # no data — never exclude on a guess
        return low <= capacity <= high

    return [fits]


def _aircon_rules(need: GenericNeed) -> list[Predicate]:
    """Máy lạnh: room area (m²) must fall inside 'Phạm vi sử dụng' (a range
    like 'Từ 30 - 40m²'); products stating a range that excludes the room are
    dropped."""
    answer = need.attribute_constraints.get("room_area")
    area = _first_number(answer)
    if area is None:
        return []

    def covers(product: GenericProduct) -> bool:
        bounds = _numbers(product.attributes.get("Phạm vi sử dụng"))
        if len(bounds) < 2:
            return True
        low, high = bounds[0], bounds[1]
        return low <= area <= high

    return [covers]


def _monitor_rules(need: GenericNeed) -> list[Predicate]:
    """Màn hình: requested size (inch) within ±2 inch of 'Kích thước màn hình'."""
    answer = need.attribute_constraints.get("size")
    size = _first_number(answer)
    if size is None:
        return []

    def close_enough(product: GenericProduct) -> bool:
        actual = _first_number(product.attributes.get("Kích thước màn hình"))
        if actual is None:
            return True
        return abs(actual - size) <= 2.0

    return [close_enough]


_RULES: dict[str, Callable[[GenericNeed], list[Predicate]]] = {
    "38": _fridge_rules,
    "36": _aircon_rules,
    "73": _monitor_rules,
}


def derive_predicates(need: GenericNeed) -> list[Predicate]:
    rule = _RULES.get(need.category_code or "")
    return rule(need) if rule else []


def apply_domain_filters(
    products: list[GenericProduct], need: GenericNeed
) -> list[GenericProduct]:
    predicates = derive_predicates(need)
    if not predicates:
        return products
    filtered = [
        product
        for product in products
        if all(predicate(product) for predicate in predicates)
    ]
    # Never let a domain rule empty the pool entirely — degrade to unfiltered.
    return filtered or products
