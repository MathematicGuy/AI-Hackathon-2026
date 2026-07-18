"""Suggestion roles: preference-driven dimensions over the fixed trio.

Baseline (no preference signal) keeps the classic behavior: best_price,
best_value, and a generic best-performance pick — additive only, so the
flows that already worked stay untouched. When the captured need points at
concrete dimensions ("chơi game", "êm", "tiết kiệm điện"), up to two
dimension roles replace the generic performance pick, each carrying evidence
(label + the real spec value) so the customer sees WHAT was measured
(Cường's live-test 3: metric transparency).
"""

import re
from dataclasses import dataclass, field

from backend.app.agent.catalog.dataset_adapter import GenericProduct
from backend.app.agent.catalog.dimensions import (
    Dimension,
    dimension_display,
    dimension_value,
    find_dimension,
    headline_dimension,
    preferred_dimensions,
    rankable,
)
from backend.app.agent.contracts import DEFAULT_ROLES
from backend.app.agent.conversation.coldstart import performance_attribute

_NUMBER = re.compile(r"(\d+(?:[.,]\d+)?)")

# A dimension role is only offered when at least this share of the pool has
# real data for it — never rank a mostly-empty column.
MIN_DATA_SHARE = 0.3


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
    # role -> (display label, real spec value backing the pick)
    role_evidence: dict[str, tuple[str, str]] = field(default_factory=dict)

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


def _dynamic_roles(category_code: str, need) -> tuple[str, ...]:
    """No stated roles: classic trio unless the need names dimensions."""
    preferred = [
        dim for dim in preferred_dimensions(category_code, need) if rankable(dim)
    ][:2]
    if not preferred:
        return DEFAULT_ROLES
    return ("best_price", "best_value") + tuple(
        f"dim:{dim.key}" for dim in preferred
    )


def _dimension_winner(
    candidates: list[GenericProduct], dim: Dimension
) -> GenericProduct | None:
    valued = [
        (value, product)
        for product in candidates
        if (value := dimension_value(product, dim)) is not None
    ]
    if not candidates or len(valued) / len(candidates) < MIN_DATA_SHARE:
        return None
    if dim.kind == "numeric_lower":
        return min(valued, key=lambda entry: (entry[0], entry[1].productidweb))[1]
    if dim.kind == "feature":
        winners = [p for value, p in valued if value]
        priced = [p for p in winners if p.effective_price is not None]
        pool = priced or winners
        return min(pool, key=lambda p: (p.effective_price or 0, p.productidweb)) if pool else None
    return max(valued, key=lambda entry: (entry[0], entry[1].productidweb))[1]


def suggest_products(
    candidates: list[GenericProduct],
    *,
    category_code: str,
    roles: tuple[str, ...] | list[str] | None = None,
    need=None,
) -> Suggestions:
    selected_roles = (
        tuple(roles) if roles else _dynamic_roles(category_code, need)
    )
    priced = [p for p in candidates if p.effective_price is not None]
    winners: dict[str, GenericProduct] = {}
    skipped: list[str] = []
    evidence: dict[str, tuple[str, str]] = {}

    for role in selected_roles:
        if role == "best_price":
            if priced:
                winners[role] = min(
                    priced, key=lambda p: (p.effective_price, p.productidweb)
                )
            else:
                skipped.append(role)
        elif role == "most_expensive":
            if priced:
                winners[role] = max(
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
        elif role.startswith("dim:"):
            dim = find_dimension(category_code, role.removeprefix("dim:"))
            winner = _dimension_winner(candidates, dim) if dim else None
            if winner is not None:
                winners[role] = winner
                shown = dimension_display(winner, dim)
                evidence[role] = (dim.superlative or dim.label, shown or "")
            else:
                skipped.append(role)
        elif role == "best_performance":
            # Prefer the category's headline dimension (transparent, ordinal-
            # aware); legacy numeric performance_attribute stays as fallback.
            dim = headline_dimension(category_code)
            winner = (
                _dimension_winner(candidates, dim)
                if dim is not None and rankable(dim)
                else None
            )
            if winner is not None:
                winners[role] = winner
                shown = dimension_display(winner, dim)
                evidence[role] = (dim.superlative or dim.label, shown or "")
                continue
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

    return Suggestions(
        winners=winners, skipped_roles=skipped, role_evidence=evidence
    )
