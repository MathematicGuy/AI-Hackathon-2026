"""Deterministic price and promotion parsing. Malformed values become None —
the agent never guesses a price."""

import re
from dataclasses import dataclass

_DIGITS = re.compile(r"^\d+$")


def parse_vnd(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, float):
        return int(value) if value >= 0 and value.is_integer() else None
    if isinstance(value, str):
        cleaned = value.strip().lower()
        if not cleaned or cleaned in ("null", "none"):
            return None
        cleaned = re.sub(r"(vnd|vnđ|đ|d)$", "", cleaned).strip()
        cleaned = cleaned.replace(".", "").replace(",", "").replace(" ", "")
        if _DIGITS.match(cleaned):
            return int(cleaned)
    return None


@dataclass(frozen=True, slots=True)
class PromotionInfo:
    list_price: int | None
    sale_price: int | None
    gift: str | None

    @property
    def discount_percent(self) -> float | None:
        if self.list_price and self.sale_price and self.sale_price < self.list_price:
            return (self.list_price - self.sale_price) * 100.0 / self.list_price
        return None

    @property
    def effective_price(self) -> int | None:
        return self.sale_price if self.sale_price is not None else self.list_price


def extract_promotion(row: dict) -> PromotionInfo:
    gift_raw = row.get("khuyến mãi quà")
    gift = str(gift_raw).strip() if gift_raw not in (None, "") else None
    return PromotionInfo(
        list_price=parse_vnd(row.get("giá gốc")),
        sale_price=parse_vnd(row.get("giá khuyến mãi")),
        gift=gift,
    )
