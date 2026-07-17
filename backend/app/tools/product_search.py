"""Stable cursor search over an injected product catalog."""

from dataclasses import dataclass

from backend.app.contracts.schemas import ProductSearchResult

from .catalog_adapter import CatalogAdapter


@dataclass(frozen=True, slots=True)
class AirConditionerFilters:
    category: str = "air_conditioner"
    region_code: str | None = None

    def __post_init__(self) -> None:
        if self.category != "air_conditioner":
            raise ValueError("category must be air_conditioner")


def _validate_page_request(limit: int, cursor: int) -> None:
    valid_limit = isinstance(limit, int) and not isinstance(limit, bool)
    valid_cursor = isinstance(cursor, int) and not isinstance(cursor, bool)
    if not valid_limit or not 1 <= limit <= 10 or not valid_cursor or cursor < 0:
        raise ValueError("invalid page request")


def _one_snapshot(records: list[dict]) -> str:
    snapshots = [record.get("source_snapshot") for record in records]
    if not snapshots or any(
        not isinstance(snapshot, str) or not snapshot for snapshot in snapshots
    ):
        raise ValueError("catalog records must share one source_snapshot")
    if any(snapshot != snapshots[0] for snapshot in snapshots[1:]):
        raise ValueError("catalog records must share one source_snapshot")
    return snapshots[0]


def search_air_conditioners(
    filters: AirConditionerFilters,
    *,
    adapter: CatalogAdapter,
    limit: int = 3,
    cursor: int = 0,
    exclude_product_ids: list[str] | None = None,
) -> ProductSearchResult:
    _validate_page_request(limit, cursor)
    catalog = adapter.load()
    if not isinstance(catalog, list):
        raise ValueError("catalog must be a list")
    if any(not isinstance(record, dict) for record in catalog):
        raise ValueError("catalog records must be objects")
    if any(
        not isinstance(record.get("product_id"), str)
        or not record["product_id"]
        for record in catalog
    ):
        raise ValueError("catalog records must have a non-empty string product_id")

    candidates = [
        record
        for record in catalog
        if record.get("category") == filters.category
        and (
            filters.region_code is None
            or record.get("region_code") == filters.region_code
        )
    ]
    source_snapshot = _one_snapshot(candidates or catalog)
    excluded = set(exclude_product_ids or ())
    page = []
    scan = min(cursor, len(candidates))

    while scan < len(candidates) and len(page) < limit:
        record = candidates[scan]
        scan += 1
        if record.get("product_id") not in excluded:
            page.append(record)

    has_more = any(
        record["product_id"] not in excluded for record in candidates[scan:]
    )
    return ProductSearchResult(
        products=page,
        next_cursor=scan if has_more else None,
        total_candidates=len(candidates),
        has_more=has_more,
        source_snapshot=source_snapshot,
    )
