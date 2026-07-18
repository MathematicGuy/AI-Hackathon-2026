from __future__ import annotations

import copy
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping, MutableMapping, TypeVar


SKIPPED_OUT_OF_STOCK = "skipped_out_of_stock"
SELLABLE_STOCK_STATUSES = frozenset(
    {"in_stock", "limited", "preorder", "listed_with_hanoi_price"}
)
TERMINAL_CHECKPOINT_STATUSES = frozenset({"success", SKIPPED_OUT_OF_STOCK})

ItemT = TypeVar("ItemT", bound=Mapping[str, Any])
PayloadT = TypeVar("PayloadT")


@dataclass(frozen=True)
class InventoryBatchResult:
    requested: int
    persisted: int
    skipped_out_of_stock: int
    resumed_terminal: int


def is_sellable_stock(status: Any) -> bool:
    return str(status or "").strip().casefold() in SELLABLE_STOCK_STATUSES


def is_out_of_stock(status: Any) -> bool:
    return str(status or "").strip().casefold() == "out_of_stock"


def should_request_checkpoint_result(result: Mapping[str, Any] | None) -> bool:
    return str((result or {}).get("status") or "pending") not in TERMINAL_CHECKPOINT_STATUSES


def _payload_stock_status(payload: Any) -> str:
    if isinstance(payload, Mapping):
        return str(payload.get("stock_status") or "")
    snapshot = getattr(payload, "snapshot", None)
    if snapshot is not None:
        return str(getattr(snapshot, "stock_status", "") or "")
    return str(getattr(payload, "stock_status", "") or "")


def run_inventory_batch(
    items: Iterable[ItemT],
    results: MutableMapping[str, dict[str, Any]],
    fetch_parse: Callable[[ItemT], PayloadT],
    persist_payload: Callable[[ItemT, PayloadT], Mapping[str, Any]],
    record_inventory_skip: Callable[[ItemT, PayloadT], None],
) -> InventoryBatchResult:
    """Process stock outcomes while propagating genuine system failures."""

    requested = persisted = skipped = resumed = 0
    for item in items:
        key = str(item["url"])
        if not should_request_checkpoint_result(results.get(key)):
            resumed += 1
            continue
        payload = fetch_parse(item)
        requested += 1
        stock_status = _payload_stock_status(payload)
        if is_out_of_stock(stock_status):
            record_inventory_skip(item, payload)
            results[key] = {
                "status": SKIPPED_OUT_OF_STOCK,
                "reason": "out_of_stock",
                "stock_status": "out_of_stock",
            }
            skipped += 1
            continue
        if not is_sellable_stock(stock_status):
            raise ValueError(f"unconfirmed sellable stock status: {stock_status or 'missing'}")
        result = dict(persist_payload(item, payload))
        result["status"] = "success"
        results[key] = result
        persisted += 1
    return InventoryBatchResult(requested, persisted, skipped, resumed)


def _normalized(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").casefold())
    text = "".join(character for character in text if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _selection_type(item: Mapping[str, Any]) -> str:
    explicit = str(item.get("selection_type") or "").strip()
    if explicit:
        return explicit
    for membership in item.get("memberships") or []:
        value = str(membership)
        if value.startswith("Loại: "):
            return value.removeprefix("Loại: ").strip()
    return "Listing chung"


def _variant_signature(item: Mapping[str, Any]) -> str:
    title = _normalized(item.get("title"))
    color_words = {
        "bac", "den", "do", "gold", "gray", "grey", "hong", "silver", "trang", "vang", "xam", "xanh",
    }
    return " ".join(word for word in title.split() if word not in color_words)


def rank_replacement_candidates(
    candidates: Iterable[Mapping[str, Any]],
    selected: Iterable[Mapping[str, Any]],
    removed: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Rank unique laptop replacements by use case, price band, then brand."""

    selected_rows = [dict(item) for item in selected if item.get("url") != removed.get("url")]
    selected_urls = {str(item.get("url")) for item in selected_rows}
    selected_keys = {str(item.get("source_product_key")) for item in selected_rows if item.get("source_product_key")}
    selected_models = {_normalized(item.get("model_hint")) for item in selected_rows if item.get("model_hint")}
    selected_variants = {_variant_signature(item) for item in selected_rows if _variant_signature(item)}
    brand_counts = Counter(str(item.get("brand") or "") for item in selected_rows)
    target_type = _normalized(_selection_type(removed))
    target_band = str(removed.get("price_band") or removed.get("_band") or "mid")
    target_brand = _normalized(removed.get("brand"))
    target_price = int(removed.get("sale_price") or 0)
    band_order = {"low": 0, "mid": 1, "high": 2}

    ranked: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    for raw in candidates:
        item = dict(raw)
        if item.get("category") != "laptop":
            continue
        url = str(item.get("url") or "")
        source_key = str(item.get("source_product_key") or "")
        model = _normalized(item.get("model_hint"))
        variant = _variant_signature(item)
        if not url or url in selected_urls or not source_key or source_key in selected_keys:
            continue
        if model and model in selected_models:
            continue
        if variant and variant in selected_variants:
            continue
        if int(item.get("sale_price") or 0) <= 0:
            continue
        if item.get("listing_location_evidence") != "confirmed_session":
            continue
        if not is_sellable_stock(item.get("stock_status")):
            continue
        candidate_type = _normalized(_selection_type(item))
        candidate_band = str(item.get("price_band") or item.get("_band") or "mid")
        score = (
            0 if candidate_type == target_type else 1,
            abs(band_order.get(candidate_band, 1) - band_order.get(target_band, 1)),
            0 if _normalized(item.get("brand")) == target_brand else 1,
            brand_counts[str(item.get("brand") or "")],
            abs(int(item.get("sale_price") or 0) - target_price),
            -int(item.get("sold") or 0),
            url,
        )
        item["selection_type"] = _selection_type(item)
        item["price_band"] = candidate_band
        item["replacement_reason"] = (
            f"use_case={item['selection_type']}; price_band={candidate_band}; "
            f"brand={item.get('brand')}; Hanoi listing sale_price and stock evidence present"
        )
        ranked.append((score, item))
    return [item for _, item in sorted(ranked, key=lambda pair: pair[0])]


def revise_locked_selection(
    checkpoint: MutableMapping[str, Any],
    replacements: Mapping[str, Mapping[str, Any]],
    *,
    created_at: str,
) -> None:
    """Create an explicit immutable-history selection revision in-place."""

    current = [dict(item) for item in checkpoint.get("selected") or []]
    if not current:
        raise ValueError("checkpoint has no locked selection")
    if not replacements:
        raise ValueError("at least one replacement is required")
    current_urls = {str(item["url"]) for item in current}
    if not set(replacements).issubset(current_urls):
        raise ValueError("replacement target is not in the current selection")
    replacement_urls = [str(item["url"]) for item in replacements.values()]
    if len(replacement_urls) != len(set(replacement_urls)):
        raise ValueError("replacement URLs must be unique")
    retained_urls = current_urls - set(replacements)
    if retained_urls.intersection(replacement_urls):
        raise ValueError("replacement duplicates a retained URL")

    if "original_selected" not in checkpoint:
        checkpoint["original_selected"] = copy.deepcopy(current)
    revisions = checkpoint.setdefault("selection_revisions", [])
    if not revisions:
        revisions.append(
            {
                "revision": 1,
                "created_at": checkpoint.get("locked_at"),
                "reason": "original locked selection",
                "selected_urls": [item["url"] for item in checkpoint["original_selected"]],
            }
        )

    revised = [dict(replacements.get(str(item["url"]), item)) for item in current]
    if len(revised) != len(current):
        raise AssertionError("selection size changed")
    if Counter(item["category"] for item in revised) != Counter(item["category"] for item in current):
        raise ValueError("replacement changed category quotas")
    if len({str(item["url"]) for item in revised}) != len(revised):
        raise ValueError("revised selection contains duplicate URLs")

    results = checkpoint.setdefault("results", {})
    removed_rows = []
    replacement_rows = []
    for old_url, replacement in replacements.items():
        old = next(item for item in current if item["url"] == old_url)
        results[old_url] = {
            **dict(results.get(old_url) or {}),
            "status": SKIPPED_OUT_OF_STOCK,
            "reason": "out_of_stock",
        }
        results[str(replacement["url"])] = {"status": "pending"}
        removed_rows.append({"url": old_url, "reason": "out_of_stock", "slot": old})
        replacement_rows.append(
            {
                "url": replacement["url"],
                "reason": replacement.get("replacement_reason"),
                "slot": dict(replacement),
            }
        )
    for item in revised:
        url = str(item["url"])
        prior = dict(results.get(url) or {})
        if prior.get("status") not in TERMINAL_CHECKPOINT_STATUSES:
            results[url] = {**prior, "status": "pending"}

    revision_number = max(int(row.get("revision", 0)) for row in revisions) + 1
    revisions.append(
        {
            "revision": revision_number,
            "created_at": created_at,
            "reason": "replace out-of-stock laptop quota slots",
            "removed": removed_rows,
            "replacements": replacement_rows,
            "selected_urls": [item["url"] for item in revised],
        }
    )
    checkpoint["selected"] = revised
    checkpoint["selection_revision"] = revision_number
    checkpoint["version"] = max(2, int(checkpoint.get("version") or 1))
    checkpoint["status"] = "locked"
