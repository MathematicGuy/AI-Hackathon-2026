"""Deterministic suggestion roles: best_price, best_value, best_performance.

Default roles per Cường's direction; the user's stated preference
(`GenericNeed.requested_roles`, e.g. "rẻ nhất" → best_price only) overrides.
best_performance uses the category's configured performance attribute; when no
candidate exposes it, the role is skipped and disclosed rather than guessed.
"""

import re
from dataclasses import dataclass, field

from backend.app.agent.catalog.dataset_adapter import GenericProduct
from backend.app.agent.contracts import DEFAULT_ROLES
from backend.app.agent.conversation.coldstart import performance_attribute

_NUMBER = re.compile(r"(\d+(?:[.,]\d+)?)")


def _performance_score(product: GenericProduct, attribute: str) -> float | None:
    value = product.attributes.get(attribute)
    if value in (None, ""):
        return None
    match = _NUMBER.search(str(value))
    if not match:
        return None
    return float(match.group(1).replace(",", "."))


@dataclass(frozen=True, slots=True)
class Suggestions:
    winners: dict[str, GenericProduct]
    skipped_roles: list[str] = field(default_factory=list)

    @property
    def distinct_products(self) -> list[GenericProduct]:
        seen: dict[str, GenericProduct] = {}
        for product in self.winners.values():
            seen.setdefault(product.productidweb, product)
        return list(seen.values())

    def roles_for(self, productidweb: str) -> list[str]:
        return [
            role
            for role, product in self.winners.items()
            if product.productidweb == productidweb
        ]


def suggest_products(
    candidates: list[GenericProduct],
    *,
    category_code: str,
    roles: tuple[str, ...] | list[str] | None = None,
) -> Suggestions:
    selected_roles = tuple(roles) if roles else DEFAULT_ROLES
    priced = [p for p in candidates if p.effective_price is not None]
    winners: dict[str, GenericProduct] = {}
    skipped: list[str] = []

    for role in selected_roles:
        if role == "best_price":
            if priced:
                winners[role] = min(
                    priced, key=lambda p: (p.effective_price, p.productidweb)
                )
            else:
                skipped.append(role)
        elif role == "best_value":
            discounted = [
                p for p in priced if p.promotion.discount_percent is not None
            ]
            if discounted:
                winners[role] = max(
                    discounted,
                    key=lambda p: (
                        p.promotion.discount_percent,
                        p.gift_promotion is not None,
                        -p.effective_price,
                        p.productidweb,
                    ),
                )
            elif gifted := [p for p in priced if p.gift_promotion]:
                winners[role] = min(
                    gifted, key=lambda p: (p.effective_price, p.productidweb)
                )
            else:
                skipped.append(role)
        elif role == "best_performance":
            attribute = performance_attribute(category_code)
            scored = []
            if attribute:
                for product in candidates:
                    score = _performance_score(product, attribute)
                    if score is not None:
                        scored.append((score, product))
            if scored:
                winners[role] = max(
                    scored, key=lambda entry: (entry[0], entry[1].productidweb)
                )[1]
            else:
                skipped.append(role)
        else:
            skipped.append(role)

    return Suggestions(winners=winners, skipped_roles=skipped)
