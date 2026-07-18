from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Generic, Mapping, TypeVar

from .db import Database, utcnow
from .models import LocationSnapshot, ProductContent, ProductLink
from .utils import fingerprint


LOCATION_TASK_TYPE = "location_product"
SKIPPED_OUT_OF_STOCK = "skipped_out_of_stock"

PayloadT = TypeVar("PayloadT")
WriteT = TypeVar("WriteT")


@dataclass(frozen=True)
class LocationCrawlPayload:
    """One fetched and parsed product payload shared by both databases."""

    link: ProductLink
    content: ProductContent
    snapshot: LocationSnapshot
    request_url: str
    response_url: str
    http_status: int
    latency_ms: int | None = None
    response_hash: str | None = None
    response_metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LocationPersistResult:
    product_id: str
    task_id: str
    content_version_id: str
    location_version_id: str
    content_changed: bool
    location_changed: bool
    content_hash: str
    state_hash: str


@dataclass(frozen=True)
class InventorySkipResult:
    task_id: str
    attempt_id: int | None


@dataclass(frozen=True)
class DualWriteResult(Generic[PayloadT, WriteT]):
    status: str
    payload: PayloadT
    neon: WriteT | None = None
    sqlite: WriteT | None = None
    error: Exception | None = None

    @property
    def reconciliation_required(self) -> bool:
        return self.status == "reconciliation_required"


class DualWriteCoordinator(Generic[PayloadT, WriteT]):
    """Fetch once, then write Neon before the SQLite mirror.

    Cross-database atomicity is intentionally not implied. A Neon failure stops
    before SQLite; a SQLite failure preserves Neon and returns a reconciliation
    marker without invoking the fetch callback again.
    """

    def execute(
        self,
        fetch_parse: Callable[[], PayloadT],
        write_neon: Callable[[PayloadT], WriteT],
        write_sqlite: Callable[[PayloadT], WriteT],
    ) -> DualWriteResult[PayloadT, WriteT]:
        payload = fetch_parse()
        try:
            neon = write_neon(payload)
        except Exception as error:
            return DualWriteResult(status="neon_failed", payload=payload, error=error)
        try:
            sqlite = write_sqlite(payload)
        except Exception as error:
            return DualWriteResult(
                status="reconciliation_required",
                payload=payload,
                neon=neon,
                error=error,
            )
        return DualWriteResult(status="success", payload=payload, neon=neon, sqlite=sqlite)


def persist_location_payload(
    database: Database,
    run_id: str,
    location_code: str,
    payload: LocationCrawlPayload,
    *,
    requested_location: str | None = None,
    returned_location: Mapping[str, Any] | None = None,
) -> LocationPersistResult:
    """Atomically persist one payload inside its target database."""

    with database.transaction():
        return _persist_location_payload_uncommitted(
            database, run_id, location_code, payload,
            requested_location=requested_location, returned_location=returned_location,
        )


def record_inventory_skip(
    database: Database,
    run_id: str,
    location_code: str,
    *,
    request_url: str,
    response_url: str,
    http_status: int,
    latency_ms: int | None = None,
    returned_location: Mapping[str, Any] | None = None,
    response_metadata: Mapping[str, Any] | None = None,
) -> InventorySkipResult:
    """Record a normal out-of-stock audit without creating catalog payload."""

    with database.transaction():
        location_id = database.location_id(location_code)
        task_id = database.create_task(
            run_id, LOCATION_TASK_TYPE, request_url, location_id=location_id,
            url=request_url, max_attempts=3,
        )
        metadata = dict(response_metadata or {})
        metadata["inventory"] = {"status": "out_of_stock", "persisted": False}
        attempt_id = database.record_attempt(
            task_id, 1, utcnow(), SKIPPED_OUT_OF_STOCK, request_url,
            response_url=response_url, http_status=http_status, latency_ms=latency_ms,
            requested_location=location_code, returned_location=returned_location or {},
            location_matched=True, response_metadata=metadata,
        )
        database.mark_task(task_id, SKIPPED_OUT_OF_STOCK)
    return InventorySkipResult(task_id=task_id, attempt_id=attempt_id)


def _persist_location_payload_uncommitted(
    database: Database,
    run_id: str,
    location_code: str,
    payload: LocationCrawlPayload,
    *,
    requested_location: str | None = None,
    returned_location: Mapping[str, Any] | None = None,
) -> LocationPersistResult:
    """Persist common and location data under the schema-valid task type."""

    product_id = database.upsert_product(payload.link)
    location_id = database.location_id(location_code)
    task_id = database.create_task(
        run_id,
        LOCATION_TASK_TYPE,
        f"{product_id}:{location_code}",
        product_id=product_id,
        location_id=location_id,
        url=payload.request_url,
        max_attempts=3,
    )
    response_hash = payload.response_hash or fingerprint(
        {"content": asdict(payload.content), "location": asdict(payload.snapshot)}
    )
    content_version_id, content_changed = database.record_content(
        product_id,
        payload.content,
        task_id=task_id,
        response_hash=response_hash,
    )
    location_version_id, location_changed = database.record_location(
        product_id,
        location_id,
        payload.snapshot,
        task_id=task_id,
        response_hash=response_hash,
    )
    database.record_attempt(
        task_id,
        1,
        utcnow(),
        "success",
        payload.request_url,
        response_url=payload.response_url,
        http_status=payload.http_status,
        latency_ms=payload.latency_ms,
        requested_location=requested_location or location_code,
        returned_location=returned_location or {},
        location_matched=True,
        response_metadata=payload.response_metadata,
    )
    database.mark_task(
        task_id,
        "succeeded" if content_changed or location_changed else "unchanged",
    )
    content_row = database.fetchone(
        "SELECT content_hash FROM {product_content_versions} WHERE id=?",
        (content_version_id,),
    )
    location_row = database.fetchone(
        "SELECT state_hash FROM {product_location_versions} WHERE id=?",
        (location_version_id,),
    )
    if not content_row or not location_row:
        raise RuntimeError("persisted current version hashes were not readable")
    return LocationPersistResult(
        product_id=product_id,
        task_id=task_id,
        content_version_id=content_version_id,
        location_version_id=location_version_id,
        content_changed=content_changed,
        location_changed=location_changed,
        content_hash=str(content_row["content_hash"]),
        state_hash=str(location_row["state_hash"]),
    )
