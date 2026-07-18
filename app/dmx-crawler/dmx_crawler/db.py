from __future__ import annotations

import contextlib
import json
import logging
import os
import sqlite3
import uuid
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Optional

from .models import CategoryConfig, LocationConfig, LocationSnapshot, ProductContent, ProductLink
from .utils import canonical_url, fingerprint, safe_json, slug_text, url_hash


LOGGER = logging.getLogger(__name__)

CATALOG_TABLES = frozenset(
    {
        "categories",
        "locations",
        "media_assets",
        "product_content_versions",
        "product_location_versions",
        "product_spec_values",
        "product_version_media",
        "products",
        "spec_definitions",
    }
)

CRAWLER_TABLES = frozenset(
    {
        "crawl_attempts",
        "crawl_errors",
        "crawl_observations",
        "crawl_runs",
        "crawl_tasks",
        "discovery_sources",
        "product_crawl_state",
        "product_location_crawl_state",
        "product_urls",
    }
)

POSTGRES_TABLE_SCHEMAS = {
    **{table: "catalog" for table in CATALOG_TABLES},
    **{table: "crawler" for table in CRAWLER_TABLES},
}
APPLICATION_TABLES = frozenset(POSTGRES_TABLE_SCHEMAS)
ALLOWED_TASK_TYPES = frozenset({"discover", "common_product", "location_product"})


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uuid() -> str:
    return str(uuid.uuid4())


def _spec_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_spec_items(specs: Any) -> list[dict[str, Any]]:
    """Return a stable flat list from legacy maps, flat items, or group snapshots."""

    if isinstance(specs, Mapping) and "items" in specs:
        specs = [specs]
    elif isinstance(specs, Mapping):
        return [
            {
                "group": "",
                "group_ordinal": 0,
                "label": str(label),
                "raw_label": str(label),
                "value": "" if value is None else str(value),
                "raw_value": "" if value is None else str(value),
                "item_ordinal": index,
                "source": "dom",
                "provenance": ["dom"],
            }
            for index, (label, value) in enumerate(specs.items())
        ]
    if not isinstance(specs, (list, tuple)):
        return []

    result: list[dict[str, Any]] = []

    def append_item(
        raw: Mapping[str, Any],
        fallback_ordinal: int,
        group_name: str = "",
        group_ordinal: int = 0,
        group_source: str = "dom",
        group_provenance: Any = None,
    ) -> None:
        item = dict(raw)
        label = item.get("label", item.get("raw_label", ""))
        value = item.get("value")
        if value is None:
            value = item.get("value_text", item.get("raw_value", ""))
        raw_value = item.get("raw_value", value)
        source = item.get("source", group_source or "dom")
        if isinstance(source, (list, tuple)):
            source = source[0] if source else "dom"
        provenance = item.get("provenance", item.get("sources", group_provenance))
        if provenance is None:
            provenance = [source]
        elif isinstance(provenance, str):
            provenance = [provenance]
        else:
            provenance = list(provenance)
        item.update(
            {
                "group": str(item.get("group", item.get("group_name", group_name)) or ""),
                "group_ordinal": _spec_int(
                    item.get("group_ordinal", item.get("groupOrdinal", group_ordinal)), group_ordinal
                ),
                "label": "" if label is None else str(label),
                "raw_label": "" if item.get("raw_label", label) is None else str(item.get("raw_label", label)),
                "value": "" if value is None else str(value),
                "raw_value": "" if raw_value is None else str(raw_value),
                "item_ordinal": _spec_int(
                    item.get("item_ordinal", item.get("ordinal", fallback_ordinal)), fallback_ordinal
                ),
                "source": str(source or "dom"),
                "provenance": [str(entry) for entry in provenance if entry],
            }
        )
        if not item["provenance"]:
            item["provenance"] = [item["source"]]
        result.append(item)

    for outer_ordinal, raw in enumerate(specs):
        if not isinstance(raw, Mapping):
            continue
        nested = raw.get("items")
        if isinstance(nested, Mapping):
            nested = [{"label": label, "value": value} for label, value in nested.items()]
        if isinstance(nested, (list, tuple)) and "label" not in raw and "raw_label" not in raw:
            group_name = str(raw.get("group", raw.get("name", "")) or "")
            group_ordinal = _spec_int(raw.get("group_ordinal", raw.get("ordinal", outer_ordinal)), outer_ordinal)
            group_source = str(raw.get("source", "dom") or "dom")
            group_provenance = raw.get("provenance", raw.get("sources", [group_source]))
            for item_ordinal, item in enumerate(nested):
                if isinstance(item, Mapping):
                    append_item(
                        item,
                        item_ordinal,
                        group_name=group_name,
                        group_ordinal=group_ordinal,
                        group_source=group_source,
                        group_provenance=group_provenance,
                    )
            continue
        append_item(raw, outer_ordinal)
    return result


def _merge_normalized_spec_items(primary: list[dict[str, Any]], secondary: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reconcile snapshot and flat views without dropping a newly observed item.

    The nested snapshot is authoritative for raw text and order. The flat view
    can contribute typed/provenance fields when the snapshot came from an older
    caller. A position-aware key preserves duplicate labels and values.
    """

    result = [dict(item) for item in primary]
    lookup: dict[tuple[int, str, int, str], dict[str, Any]] = {}
    for item in result:
        key = (
            _spec_int(item.get("group_ordinal")),
            str(item.get("group", "") or ""),
            _spec_int(item.get("item_ordinal")),
            str(item.get("label", "") or ""),
        )
        lookup[key] = item
    for incoming in secondary:
        key = (
            _spec_int(incoming.get("group_ordinal")),
            str(incoming.get("group", "") or ""),
            _spec_int(incoming.get("item_ordinal")),
            str(incoming.get("label", "") or ""),
        )
        existing = lookup.get(key)
        if existing is None:
            lookup[key] = dict(incoming)
            result.append(lookup[key])
            continue
        for field_name, value in incoming.items():
            if field_name not in existing or existing[field_name] in (None, "", []):
                existing[field_name] = value
        provenance = list(dict.fromkeys(list(existing.get("provenance", [])) + list(incoming.get("provenance", []))))
        if provenance:
            existing["provenance"] = provenance
    return sorted(
        result,
        key=lambda item: (
            _spec_int(item.get("group_ordinal")),
            _spec_int(item.get("item_ordinal")),
            str(item.get("label", "")),
        ),
    )


def _spec_snapshot(items: list[dict[str, Any]], supplied: Any = None) -> list[dict[str, Any]]:
    """Build the ordered, replayable group snapshot required by the content row."""

    groups: dict[tuple[int, str], dict[str, Any]] = {}
    group_order: list[tuple[int, str]] = []
    if isinstance(supplied, (list, tuple)):
        for index, group in enumerate(supplied):
            if not isinstance(group, Mapping):
                continue
            name = str(group.get("group", group.get("name", "")) or "")
            ordinal = _spec_int(group.get("ordinal", group.get("group_ordinal", index)), index)
            key = (ordinal, name)
            if key not in groups:
                snapshot_group: dict[str, Any] = {
                    "group": name,
                    "ordinal": ordinal,
                    "group_ordinal": ordinal,
                    "items": [],
                }
                for field_name in ("source", "sources", "provenance"):
                    if group.get(field_name) is not None:
                        snapshot_group[field_name] = group[field_name]
                groups[key] = snapshot_group
                group_order.append(key)
    for item in items:
        key = (_spec_int(item.get("group_ordinal")), str(item.get("group", "") or ""))
        if key not in groups:
            groups[key] = {"group": key[1], "ordinal": key[0], "group_ordinal": key[0], "items": []}
            group_order.append(key)
        copy: dict[str, Any] = {
            "group": key[1],
            "group_ordinal": key[0],
            "label": item.get("label", ""),
            "raw_label": item.get("raw_label", item.get("label", "")),
            "value": item.get("value", ""),
            "raw_value": item.get("raw_value", item.get("value", "")),
            "ordinal": _spec_int(item.get("item_ordinal")),
            "item_ordinal": _spec_int(item.get("item_ordinal")),
            "source": item.get("source", "dom"),
        }
        for name in ("value_text", "value_number", "value_boolean", "value_json", "unit", "provenance", "sources"):
            if name in item and item[name] is not None:
                copy[name] = item[name]
        groups[key]["items"].append(copy)
    for group in groups.values():
        group["items"].sort(key=lambda item: _spec_int(item.get("item_ordinal", item.get("ordinal", 0))))
    return [groups[key] for key in group_order]


class Database:
    """Persistence adapter for SQLite and optional PostgreSQL/psycopg.

    SQLite is useful for local samples and has no third-party dependency.  The
    PostgreSQL path uses the same repository methods after the operator applies
    migrations 001, 002, and 003. Runtime initialization verifies the split
    schema but never applies PostgreSQL migrations.
    """

    def __init__(self, url: str):
        self.url = url
        self.backend = "sqlite"
        self._initialized = False
        self._transaction_depth = 0
        if url.startswith(("postgresql://", "postgres://")):
            try:
                import psycopg  # type: ignore
                from psycopg.rows import dict_row  # type: ignore
            except ImportError as error:
                raise RuntimeError("PostgreSQL URL requires: pip install 'dmx-crawler[postgres]'") from error
            self.backend = "postgres"
            self.conn = psycopg.connect(url, row_factory=dict_row)
        else:
            path = url.removeprefix("sqlite:///") if url.startswith("sqlite:///") else url
            path = path or "data/dmx.db"
            Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(path, timeout=30, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.conn.execute("PRAGMA journal_mode = WAL")

    def _sql(self, query: str) -> str:
        for table in APPLICATION_TABLES:
            query = query.replace(f"{{{table}}}", self._relation(table))
        return query.replace("?", "%s") if self.backend == "postgres" else query

    def _relation(self, table: str) -> str:
        schema = POSTGRES_TABLE_SCHEMAS.get(table)
        if schema is None:
            raise ValueError(f"unsupported application table: {table}")
        return f"{schema}.{table}" if self.backend == "postgres" else table

    def execute(self, query: str, params: Iterable[Any] = ()):
        cursor = self.conn.cursor()
        cursor.execute(self._sql(query), tuple(params))
        return cursor

    def fetchone(self, query: str, params: Iterable[Any] = ()) -> Optional[Mapping[str, Any]]:
        row = self.execute(query, params).fetchone()
        return row

    def fetchall(self, query: str, params: Iterable[Any] = ()) -> list[Mapping[str, Any]]:
        return list(self.execute(query, params).fetchall())

    @contextlib.contextmanager
    def transaction(self) -> Iterator[None]:
        outermost = self._transaction_depth == 0
        self._transaction_depth += 1
        try:
            yield
            if outermost:
                self.conn.commit()
        except Exception:
            if outermost:
                self.conn.rollback()
            raise
        finally:
            self._transaction_depth -= 1

    def initialize(self) -> None:
        if self._initialized:
            return
        if self.backend == "sqlite":
            schema = Path(__file__).resolve().parent / "sqlite_schema.sql"
            self.conn.executescript(schema.read_text(encoding="utf-8"))
            self._initialized = True
            return

        names = sorted(APPLICATION_TABLES)
        placeholders = ",".join("?" for _ in names)
        rows = self.fetchall(
            f"""SELECT namespace.nspname AS schema_name, relation.relname AS table_name
                FROM pg_catalog.pg_class AS relation
                JOIN pg_catalog.pg_namespace AS namespace ON namespace.oid=relation.relnamespace
                WHERE relation.relkind IN ('r','p')
                  AND namespace.nspname IN ('public','catalog','crawler')
                  AND relation.relname IN ({placeholders})""",
            names,
        )
        placements: dict[str, list[str]] = {table: [] for table in names}
        for row in rows:
            placements[str(row["table_name"])].append(str(row["schema_name"]))
        discrepancies = []
        for table in names:
            expected = POSTGRES_TABLE_SCHEMAS[table]
            actual = sorted(placements[table])
            if actual != [expected]:
                found = ", ".join(f"{schema}.{table}" for schema in actual) or "missing"
                discrepancies.append(f"{table}: expected {expected}.{table}; found {found}")
        if discrepancies:
            raise RuntimeError(
                "PostgreSQL schema is not ready. Apply migrations 001, 002, and 003 "
                "outside crawler runtime; partial or legacy layouts are rejected. "
                + "; ".join(discrepancies)
            )
        self._initialized = True

    def seed_configs(self, categories: list[CategoryConfig], locations: list[LocationConfig]) -> None:
        with self.transaction():
            for category in categories:
                self.execute(
                    """INSERT INTO {categories}(code,name,active) VALUES(?,?,?)
                       ON CONFLICT(code) DO UPDATE SET name=excluded.name,active=excluded.active""",
                    (category.code, category.name, category.active),
                )
            for location in locations:
                config_hash = fingerprint(asdict(location))
                self.execute(
                    """INSERT INTO {locations}(code,name,province_id,province_name,ward_id,ward_name,address,config_hash,active)
                       VALUES(?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(code) DO UPDATE SET name=excluded.name,province_id=excluded.province_id,
                       province_name=excluded.province_name,ward_id=excluded.ward_id,ward_name=excluded.ward_name,
                       address=excluded.address,config_hash=excluded.config_hash,active=excluded.active""",
                    (location.code, location.name, location.province_id, location.province_name, location.ward_id,
                     location.ward_name, location.address, config_hash, location.active),
                )

    def category_id(self, code: str) -> int:
        row = self.fetchone("SELECT id FROM {categories} WHERE code=?", (code,))
        if not row:
            raise KeyError(f"unknown category: {code}")
        return int(row["id"])

    def location_id(self, code: str) -> int:
        row = self.fetchone("SELECT id FROM {locations} WHERE code=?", (code,))
        if not row:
            raise KeyError(f"unknown location: {code}")
        return int(row["id"])

    def create_run(self, command: str, arguments: Mapping[str, Any] | None = None, mode: str = "live", parent_run_id: str | None = None, config_hash: str | None = None) -> str:
        run_id = _uuid()
        with self.transaction():
            self.execute(
                """INSERT INTO {crawl_runs}(id,parent_run_id,command,mode,status,arguments_json,config_hash,started_at)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (run_id, parent_run_id, command, mode, "running", safe_json(arguments or {}), config_hash, utcnow()),
            )
        return run_id

    def finish_run(self, run_id: str, status: str, counters: Mapping[str, Any] | None = None, blocked_reason: str | None = None) -> None:
        with self.transaction():
            self.execute(
                "UPDATE {crawl_runs} SET status=?,counters_json=?,blocked_reason=?,finished_at=? WHERE id=?",
                (status, safe_json(counters or {}), blocked_reason, utcnow(), run_id),
            )

    def upsert_product(self, link: ProductLink) -> str:
        url = canonical_url(link.url)
        hashed = url_hash(url)
        now = utcnow()
        category_id = self.category_id(link.category_code)
        with self.transaction():
            row = None
            if link.source_product_key:
                row = self.fetchone(
                    "SELECT id FROM {products} WHERE source='dienmayxanh' AND source_product_key=?",
                    (str(link.source_product_key),),
                )
            if row is None:
                row = self.fetchone("SELECT id FROM {products} WHERE source='dienmayxanh' AND canonical_url_hash=?", (hashed,))
            if row:
                product_id = str(row["id"])
                self.execute(
                    """UPDATE {products} SET canonical_url=?,canonical_url_hash=?,category_id=?,last_seen_at=?,
                       source_product_key=COALESCE(source_product_key,?),sitemap_lastmod=COALESCE(?,sitemap_lastmod) WHERE id=?""",
                    (url, hashed, category_id, now, link.source_product_key, link.lastmod, product_id),
                )
            else:
                product_id = _uuid()
                self.execute(
                    """INSERT INTO {products}(id,source,source_product_key,canonical_url,canonical_url_hash,category_id,status,
                       first_seen_at,last_seen_at,sitemap_lastmod) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                    (product_id, "dienmayxanh", link.source_product_key, url, hashed, category_id, "active", now, now, link.lastmod),
                )
            self.execute(
                """INSERT INTO {product_urls}(product_id,source,url,url_hash,kind,first_seen_at,last_seen_at)
                   VALUES(?,?,?,?,?,?,?) ON CONFLICT(source,url_hash) DO UPDATE SET last_seen_at=excluded.last_seen_at""",
                (product_id, "dienmayxanh", url, hashed, "canonical", now, now),
            )
        return product_id

    def create_task(self, run_id: str, task_type: str, target_key: str, product_id: str | None = None, location_id: int | None = None, url: str | None = None, max_attempts: int = 3) -> str:
        if task_type not in ALLOWED_TASK_TYPES:
            raise ValueError(
                f"unsupported crawl task type: {task_type}; expected one of "
                + ", ".join(sorted(ALLOWED_TASK_TYPES))
            )
        row = self.fetchone("SELECT id FROM {crawl_tasks} WHERE run_id=? AND task_type=? AND target_key=?", (run_id, task_type, target_key))
        if row:
            return str(row["id"])
        task_id = _uuid()
        now = utcnow()
        with self.transaction():
            self.execute(
                """INSERT INTO {crawl_tasks}(id,run_id,task_type,target_key,product_id,location_id,url,status,max_attempts,
                   available_at,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (task_id, run_id, task_type, target_key, product_id, location_id, url, "queued", max_attempts, now, now),
            )
        return task_id

    def mark_task(self, task_id: str, status: str) -> None:
        finished = utcnow() if status in {"succeeded", "unchanged", "failed", "blocked", "location_mismatch", "skipped_out_of_stock"} else None
        with self.transaction():
            self.execute(
                "UPDATE {crawl_tasks} SET status=?,attempt_count=attempt_count+1,finished_at=COALESCE(?,finished_at) WHERE id=?",
                (status, finished, task_id),
            )

    def mark_failure_state(self, product_id: str, location_id: int | None = None) -> None:
        now = datetime.now(timezone.utc)
        next_due = (now + timedelta(minutes=15)).isoformat()
        with self.transaction():
            if location_id is None:
                row = self.fetchone("SELECT failure_streak FROM {product_crawl_state} WHERE product_id=?", (product_id,))
                streak = int(row["failure_streak"] if row else 0) + 1
                self.execute(
                    """INSERT INTO {product_crawl_state} AS state(product_id,last_attempt_at,next_due_at,consecutive_unchanged,failure_streak)
                       VALUES(?,?,?,?,?) ON CONFLICT(product_id) DO UPDATE SET last_attempt_at=excluded.last_attempt_at,
                       next_due_at=excluded.next_due_at,failure_streak=excluded.failure_streak""",
                    (product_id, now.isoformat(), next_due, 0, streak),
                )
            else:
                row = self.fetchone(
                    "SELECT failure_streak FROM {product_location_crawl_state} WHERE product_id=? AND location_id=?",
                    (product_id, location_id),
                )
                streak = int(row["failure_streak"] if row else 0) + 1
                self.execute(
                    """INSERT INTO {product_location_crawl_state} AS state(product_id,location_id,last_attempt_at,next_due_at,
                       consecutive_unchanged,failure_streak) VALUES(?,?,?,?,?,?)
                       ON CONFLICT(product_id,location_id) DO UPDATE SET last_attempt_at=excluded.last_attempt_at,
                       next_due_at=excluded.next_due_at,failure_streak=excluded.failure_streak""",
                    (product_id, location_id, now.isoformat(), next_due, 0, streak),
                )

    def product_rows(self, category_codes: list[str] | None = None, limit: int | None = None, only_due: bool = False, location_id: int | None = None) -> list[Mapping[str, Any]]:
        query = """SELECT p.*, c.code AS category_code FROM {products} p JOIN {categories} c ON c.id=p.category_id"""
        params: list[Any] = []
        clauses = ["p.status <> 'retired'"]
        if category_codes:
            clauses.append("c.code IN (" + ",".join("?" for _ in category_codes) + ")")
            params.extend(category_codes)
        if only_due:
            if location_id is None:
                query += " LEFT JOIN {product_crawl_state} s ON s.product_id=p.id"
                clauses.append("(s.next_due_at IS NULL OR s.next_due_at <= ?)")
            else:
                query += " LEFT JOIN {product_location_crawl_state} s ON s.product_id=p.id AND s.location_id=?"
                params.insert(0, location_id)
                clauses.append("(s.next_due_at IS NULL OR s.next_due_at <= ?)")
            params.append(utcnow())
        query += " WHERE " + " AND ".join(clauses) + " ORDER BY p.last_seen_at DESC"
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        return self.fetchall(query, params)

    def _record_observation(self, task_id: str | None, product_id: str, changed: bool, content_version_id: str | None = None, location_id: int | None = None, location_version_id: str | None = None, response_hash: str | None = None) -> None:
        self.execute(
            """INSERT INTO {crawl_observations}(task_id,product_id,location_id,content_version_id,location_version_id,
               changed,observed_at,response_hash) VALUES(?,?,?,?,?,?,?,?)""",
            (task_id, product_id, location_id, content_version_id, location_version_id, changed, utcnow(), response_hash),
        )

    def record_content(self, product_id: str, content: ProductContent, task_id: str | None = None, response_hash: str | None = None) -> tuple[str, bool]:
        category_id = self.category_id(content.category_code)
        supplied_specs = getattr(content, "specs_raw", None)
        spec_items = _normalize_spec_items(content.specs)
        snapshot_items = _normalize_spec_items(supplied_specs) if supplied_specs else []
        if snapshot_items:
            spec_items = _merge_normalized_spec_items(snapshot_items, spec_items)
        elif not spec_items and supplied_specs:
            spec_items = _normalize_spec_items(supplied_specs)
        spec_snapshot = _spec_snapshot(spec_items, supplied_specs)
        diagnostics = getattr(content, "specs_diagnostics", None) or getattr(content, "spec_diagnostics", None) or {}
        warnings = diagnostics.get("warnings", []) if isinstance(diagnostics, Mapping) else []
        if warnings:
            LOGGER.warning("spec completeness warnings for product %s: %s", product_id, warnings)
        payload = {
            "category": content.category_code,
            "name": content.name,
            "brand": content.brand,
            "model": content.model,
            "product_code": content.product_code,
            "description": content.description,
            "rating": content.rating,
            "rating_count": content.rating_count,
            "sold_count": content.sold_count,
            "specs": spec_snapshot,
            "images": content.images,
            "stock_status": content.stock_status,
            "stock_raw": content.stock_raw,
        }
        content_hash = fingerprint(payload)
        now = utcnow()
        current = self.fetchone("SELECT id,content_hash FROM {product_content_versions} WHERE product_id=? AND valid_to IS NULL", (product_id,))
        changed = not current or current["content_hash"] != content_hash
        with self.transaction():
            if changed:
                if current:
                    self.execute("UPDATE {product_content_versions} SET valid_to=? WHERE id=?", (now, current["id"]))
                version_id = _uuid()
                self.execute(
                    """INSERT INTO {product_content_versions}(id,product_id,category_id,name,brand,model,product_code,description,
                       rating,rating_count,sold_count,stock_status,stock_raw,specs_raw_json,content_hash,valid_from,created_by_task_id)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        version_id, product_id, category_id, content.name, content.brand, content.model, content.product_code,
                        content.description, content.rating, content.rating_count, content.sold_count, content.stock_status,
                        content.stock_raw, safe_json(spec_snapshot), content_hash, now, task_id,
                    ),
                )
                for global_ordinal, spec in enumerate(spec_items):
                    label = str(spec.get("label", "") or "")
                    value_text = spec.get("value_text")
                    if value_text is None:
                        value_text = spec.get("value", "")
                    value_text = "" if value_text is None else str(value_text)
                    raw_label = str(spec.get("raw_label", label) or "")
                    raw_value = str(spec.get("raw_value", value_text) or "")
                    group_name = str(spec.get("group", spec.get("group_name", "")) or "")
                    group_ordinal = _spec_int(spec.get("group_ordinal", 0))
                    item_ordinal = _spec_int(spec.get("item_ordinal", spec.get("ordinal", global_ordinal)), global_ordinal)
                    source = str(spec.get("source", "dom") or "dom")
                    provenance = spec.get("provenance", spec.get("sources", [source]))
                    if isinstance(provenance, str):
                        provenance = [provenance]
                    else:
                        provenance = list(provenance or [source])
                    value_number = spec.get("value_number")
                    value_boolean = spec.get("value_boolean")
                    value_json = spec.get("value_json")
                    if value_json is None:
                        value_json = {"text": value_text}
                    normalized_json = value_json
                    definition = None
                    if label:
                        normalized_key = slug_text(label).replace(" ", "_") or f"spec_{global_ordinal}"
                        data_type = "boolean" if isinstance(value_boolean, bool) else ("number" if value_number is not None else "text")
                        self.execute(
                            """INSERT INTO {spec_definitions}(category_id,normalized_key,canonical_label,data_type,aliases_json)
                               VALUES(?,?,?,?,?) ON CONFLICT(category_id,normalized_key) DO NOTHING""",
                            (category_id, normalized_key, label, data_type, "[]"),
                        )
                        definition = self.fetchone("SELECT id FROM {spec_definitions} WHERE category_id=? AND normalized_key=?", (category_id, normalized_key))
                    self.execute(
                        """INSERT INTO {product_spec_values}(content_version_id,definition_id,group_name,group_ordinal,
                           raw_label,raw_value,value_text,value_number,value_boolean,value_json,unit,item_ordinal,source,
                           provenance_json,normalized_value_json,ordinal) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (
                            version_id, definition["id"] if definition else None, group_name, group_ordinal,
                            raw_label, raw_value, value_text, value_number, value_boolean, safe_json(value_json),
                            spec.get("unit"), item_ordinal, source, safe_json(provenance), safe_json(normalized_json), global_ordinal,
                        ),
                    )
                for ordinal, image in enumerate(content.images):
                    media_hash = fingerprint({"url": image})
                    media = self.fetchone("SELECT id FROM {media_assets} WHERE url_hash=?", (media_hash,))
                    if media:
                        media_id = str(media["id"])
                    else:
                        media_id = _uuid()
                        self.execute("INSERT INTO {media_assets}(id,url,url_hash,metadata_json) VALUES(?,?,?,?)", (media_id, image, media_hash, "{}"))
                    self.execute(
                        """INSERT INTO {product_version_media}(content_version_id,media_id,role,ordinal) VALUES(?,?,?,?)
                           ON CONFLICT(content_version_id,media_id) DO NOTHING""",
                        (version_id, media_id, "primary" if ordinal == 0 else "gallery", ordinal),
                    )
            else:
                version_id = str(current["id"])
            state = self.fetchone("SELECT consecutive_unchanged FROM {product_crawl_state} WHERE product_id=?", (product_id,))
            unchanged = 0 if changed else int(state["consecutive_unchanged"] if state else 0) + 1
            next_due = (datetime.now(timezone.utc) + timedelta(hours=min(24 * 7, 12 * (2 ** min(unchanged, 4))))).isoformat()
            self.execute(
                """INSERT INTO {product_crawl_state} AS state(product_id,last_attempt_at,last_success_at,last_changed_at,next_due_at,last_response_hash,
                   consecutive_unchanged,failure_streak) VALUES(?,?,?,?,?,?,?,0)
                   ON CONFLICT(product_id) DO UPDATE SET last_attempt_at=excluded.last_attempt_at,last_success_at=excluded.last_success_at,
                   last_changed_at=COALESCE(excluded.last_changed_at,state.last_changed_at),next_due_at=excluded.next_due_at,
                   last_response_hash=excluded.last_response_hash,consecutive_unchanged=excluded.consecutive_unchanged,failure_streak=0""",
                (product_id, now, now, now if changed else None, next_due, response_hash, unchanged),
            )
            self.execute(
                "UPDATE {products} SET source_product_key=COALESCE(source_product_key,?),status=?,last_seen_at=? WHERE id=?",
                (content.source_product_key, "unavailable" if content.stock_status == "out_of_stock" else "active", now, product_id),
            )
            self._record_observation(task_id, product_id, changed, content_version_id=version_id, response_hash=response_hash)
        return version_id, changed

    def record_location(self, product_id: str, location_id: int, snapshot: LocationSnapshot, task_id: str | None = None, response_hash: str | None = None) -> tuple[str, bool]:
        payload = asdict(snapshot)
        payload.pop("observed_at", None)
        state_hash = fingerprint(payload)
        now = utcnow()
        current = self.fetchone(
            "SELECT id,state_hash FROM {product_location_versions} WHERE product_id=? AND location_id=? AND valid_to IS NULL",
            (product_id, location_id),
        )
        changed = not current or current["state_hash"] != state_hash
        with self.transaction():
            if changed:
                if current:
                    self.execute("UPDATE {product_location_versions} SET valid_to=? WHERE id=?", (now, current["id"]))
                version_id = _uuid()
                self.execute(
                    """INSERT INTO {product_location_versions}(id,product_id,location_id,sale_price,list_price,currency,promotion_json,
                       stock_status,stock_raw,delivery_json,returned_location_json,state_hash,valid_from,created_by_task_id)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        version_id, product_id, location_id, snapshot.sale_price, snapshot.list_price, "VND",
                        safe_json(snapshot.promotion), snapshot.stock_status, snapshot.stock_raw, safe_json(asdict(snapshot.delivery)),
                        safe_json(snapshot.returned_location), state_hash, now, task_id,
                    ),
                )
            else:
                version_id = str(current["id"])
            state = self.fetchone(
                "SELECT consecutive_unchanged FROM {product_location_crawl_state} WHERE product_id=? AND location_id=?",
                (product_id, location_id),
            )
            unchanged = 0 if changed else int(state["consecutive_unchanged"] if state else 0) + 1
            next_due = (datetime.now(timezone.utc) + timedelta(hours=min(72, 6 * (2 ** min(unchanged, 3))))).isoformat()
            self.execute(
                """INSERT INTO {product_location_crawl_state} AS state(product_id,location_id,last_attempt_at,last_success_at,last_changed_at,
                   next_due_at,last_response_hash,consecutive_unchanged,failure_streak) VALUES(?,?,?,?,?,?,?,?,0)
                   ON CONFLICT(product_id,location_id) DO UPDATE SET last_attempt_at=excluded.last_attempt_at,
                   last_success_at=excluded.last_success_at,last_changed_at=COALESCE(excluded.last_changed_at,state.last_changed_at),
                   next_due_at=excluded.next_due_at,last_response_hash=excluded.last_response_hash,
                   consecutive_unchanged=excluded.consecutive_unchanged,failure_streak=0""",
                (product_id, location_id, now, now, now if changed else None, next_due, response_hash, unchanged),
            )
            self._record_observation(
                task_id, product_id, changed, location_id=location_id, location_version_id=version_id, response_hash=response_hash
            )
        return version_id, changed

    def record_attempt(
        self,
        task_id: str | None,
        attempt_no: int,
        started_at: str,
        outcome: str,
        request_url: str,
        response_url: str | None = None,
        http_status: int | None = None,
        latency_ms: int | None = None,
        requested_location: str | None = None,
        returned_location: Mapping[str, Any] | None = None,
        location_matched: bool | None = None,
        error_kind: str | None = None,
        response_metadata: Mapping[str, Any] | None = None,
    ) -> int | None:
        query = """INSERT INTO {crawl_attempts}(task_id,attempt_no,started_at,finished_at,http_status,latency_ms,request_url,
                   response_url,requested_location,returned_location_json,location_matched,outcome,error_kind,
                   response_metadata_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
        if self.backend == "postgres":
            query += " RETURNING id"
        with self.transaction():
            cursor = self.execute(
                query,
                (
                    task_id, attempt_no, started_at, utcnow(), http_status, latency_ms, request_url, response_url,
                    requested_location, safe_json(returned_location or {}), location_matched, outcome, error_kind,
                    safe_json(response_metadata or {}),
                ),
            )
            if self.backend == "sqlite":
                return int(cursor.lastrowid)
            row = cursor.fetchone()
            return int(row["id"]) if row else None

    def record_error(
        self,
        run_id: str,
        error_kind: str,
        message: str,
        retryable: bool,
        task_id: str | None = None,
        attempt_id: int | None = None,
        product_id: str | None = None,
        location_id: int | None = None,
        http_status: int | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> None:
        with self.transaction():
            self.execute(
                """INSERT INTO {crawl_errors}(run_id,task_id,attempt_id,product_id,location_id,error_kind,message,http_status,
                   retryable,context_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (run_id, task_id, attempt_id, product_id, location_id, error_kind, message[:4000], http_status, retryable, safe_json(context or {}), utcnow()),
            )

    def retryable_errors(self, limit: int | None = None) -> list[Mapping[str, Any]]:
        query = """SELECT e.*,t.task_type,t.url,t.target_key,p.canonical_url,l.code AS location_code
                   FROM {crawl_errors} e LEFT JOIN {crawl_tasks} t ON t.id=e.task_id
                   LEFT JOIN {products} p ON p.id=e.product_id LEFT JOIN {locations} l ON l.id=e.location_id
                   WHERE e.retryable=? AND e.resolved_at IS NULL ORDER BY e.created_at"""
        params: list[Any] = [True]
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        return [dict(row) for row in self.fetchall(query, params)]

    def resolve_error(self, error_id: int, task_id: str | None = None) -> None:
        with self.transaction():
            self.execute(
                "UPDATE {crawl_errors} SET resolved_at=?,resolved_by_task_id=? WHERE id=?",
                (utcnow(), task_id, error_id),
            )

    def export_current(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.fetchall(
            """SELECT p.id,p.canonical_url,c.code AS category,pcv.id AS content_version_id,
                      pcv.name,pcv.brand,pcv.model,pcv.product_code,pcv.rating,pcv.rating_count,
                      pcv.sold_count,pcv.specs_raw_json,pcv.description,pcv.stock_status AS common_stock_status,
                      pcv.stock_raw AS common_stock_raw,
                      l.code AS location,plv.sale_price,plv.list_price,plv.promotion_json,plv.stock_status,
                      plv.stock_raw,plv.delivery_json,plv.returned_location_json,plv.valid_from AS observed_at
               FROM {products} p JOIN {categories} c ON c.id=p.category_id
               JOIN {product_content_versions} pcv ON pcv.product_id=p.id AND pcv.valid_to IS NULL
               LEFT JOIN {product_location_versions} plv ON plv.product_id=p.id AND plv.valid_to IS NULL
               LEFT JOIN {locations} l ON l.id=plv.location_id
               ORDER BY pcv.name,l.code LIMIT ?""",
            (limit,),
        )
        result: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            version_id = item.pop("content_version_id", None)
            for key in ("specs_raw_json", "promotion_json", "delivery_json", "returned_location_json"):
                raw_value = item.pop(key, None)
                if isinstance(raw_value, (dict, list)):
                    item[key.removesuffix("_json")] = raw_value
                    continue
                try:
                    item[key.removesuffix("_json")] = json.loads(raw_value or "{}")
                except (ValueError, TypeError, json.JSONDecodeError):
                    item[key.removesuffix("_json")] = {}
            if version_id:
                media_rows = self.fetchall(
                    """SELECT ma.url FROM {product_version_media} pvm
                       JOIN {media_assets} ma ON ma.id=pvm.media_id
                       WHERE pvm.content_version_id=? ORDER BY pvm.ordinal""",
                    (version_id,),
                )
                item["images"] = [str(media["url"]) for media in media_rows]
            else:
                item["images"] = []
            result.append(item)
        return result

    def table_count(self, table: str) -> int:
        relation = self._relation(table)
        row = self.fetchone(f"SELECT COUNT(*) AS n FROM {relation}")
        return int(row["n"] if row else 0)

    def close(self) -> None:
        self.conn.close()
