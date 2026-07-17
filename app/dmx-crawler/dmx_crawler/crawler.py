from __future__ import annotations

import argparse
import json
import traceback
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .adapters.dmx import DMXAdapter
from .config import Settings, load_categories, load_locations
from .db import Database
from .discovery import Discoverer
from .http import BlockedError, HTTPClientError, LocationMismatchError, RateLimiter, RespectfulClient
from .models import CategoryConfig, LocationConfig, ProductLink
from .utils import fingerprint, safe_json


@dataclass
class RunStats:
    run_id: str
    succeeded: int = 0
    unchanged: int = 0
    failed: int = 0
    blocked: int = 0
    location_mismatch: int = 0
    discovered: int = 0

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class Crawler:
    """Application service separating common product data from location state."""

    def __init__(
        self,
        settings: Settings | None = None,
        db: Database | None = None,
        categories: list[CategoryConfig] | None = None,
        locations: list[LocationConfig] | None = None,
    ) -> None:
        self.settings = settings or Settings.from_env()
        self.categories = categories or load_categories(self.settings.categories_file, self.settings.site_base_url)
        self.locations = locations or load_locations(self.settings.locations_file)
        self.db = db or Database(self.settings.database_url)
        # Independent CookieJars are mandatory; the limiter is deliberately
        # shared so separate location sessions still respect one host-wide
        # request budget.
        self.host_limiter = RateLimiter(self.settings.min_request_interval_seconds)

    def initialize(self) -> None:
        self.db.initialize()
        self.db.seed_configs(self.categories, self.locations)

    def _client(self) -> RespectfulClient:
        kwargs = dict(
            user_agent=self.settings.user_agent,
            min_interval=self.settings.min_request_interval_seconds,
            timeout=self.settings.request_timeout_seconds,
            max_attempts=self.settings.max_attempts,
        )
        try:
            return RespectfulClient(rate_limiter=self.host_limiter, **kwargs)
        except TypeError:
            # Compatibility with an older local adapter; it remains cookie
            # isolated, though a per-client limiter is less strict globally.
            return RespectfulClient(**kwargs)

    def _category_codes(self, values: Iterable[str] | None) -> list[str]:
        active = [c.code for c in self.categories if c.active]
        if not values:
            return active
        wanted = [str(v).strip() for v in values if str(v).strip()]
        unknown = sorted(set(wanted) - set(active))
        if unknown:
            raise ValueError('unknown/inactive categories: ' + ', '.join(unknown))
        return wanted

    def _location(self, code: str) -> LocationConfig:
        for location in self.locations:
            if location.code == code and location.active:
                return location
        raise ValueError(f'unknown/inactive location: {code}')

    def discover(self, category_codes: Iterable[str] | None = None, source: str = 'auto', limit: int | None = None, max_sitemaps: int | None = None) -> RunStats:
        self.initialize()
        codes = self._category_codes(category_codes)
        run_id = self.db.create_run('discover', {'categories': codes, 'source': source, 'limit': limit, 'max_sitemaps': max_sitemaps})
        stats = RunStats(run_id=run_id)
        client = self._client()
        try:
            discoverer = Discoverer(self.settings, self.categories, client)
            links = discoverer.discover(codes, source=source, limit=limit, max_sitemaps=max_sitemaps)
            for link in links:
                self.db.upsert_product(link)
            stats.discovered = len(links)
            self.db.finish_run(run_id, 'succeeded', stats.as_dict())
            return stats
        except BlockedError as exc:
            stats.blocked = 1
            self.db.record_error(run_id, 'blocked', str(exc), False, context={'stage': 'discover'})
            self.db.finish_run(run_id, 'blocked', stats.as_dict(), str(exc))
            return stats
        except Exception as exc:
            self.db.record_error(run_id, type(exc).__name__, str(exc), isinstance(exc, HTTPClientError), context={'stage': 'discover', 'traceback': traceback.format_exc()})
            self.db.finish_run(run_id, 'failed', stats.as_dict())
            raise
        finally:
            client.close()

    def _rows(self, category_codes: list[str], limit: int | None, force: bool, location_id: int | None = None, product_ids: set[str] | None = None) -> list[dict[str, Any]]:
        rows = self.db.product_rows(category_codes, limit=None if product_ids else limit, only_due=not force, location_id=location_id)
        if product_ids is not None:
            rows = [row for row in rows if str(row['id']) in product_ids]
            if limit:
                rows = rows[:limit]
        return [dict(row) for row in rows]

    @staticmethod
    def _attempt_response_metadata(content: Any | None = None, response: Any | None = None, exc: Exception | None = None) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        diagnostics = getattr(content, "specs_diagnostics", None) if content is not None else None
        if isinstance(diagnostics, dict):
            metadata["specifications"] = diagnostics
        http: dict[str, Any] = {}
        source = response if response is not None else exc
        if source is not None:
            attempts = getattr(source, "attempts", None)
            if attempts is not None:
                http["transport_attempt_count"] = attempts
            retry_after = getattr(source, "retry_after", None)
            if retry_after is not None:
                http["retry_after_seconds"] = retry_after
        if response is not None:
            content_type = getattr(response, "headers", {}).get("content-type")
            if content_type:
                http["content_type"] = content_type
            body = getattr(response, "body", None)
            if body is not None:
                http["response_bytes"] = len(body)
        if http:
            metadata["http"] = http
        return metadata

    def _record_failure(
        self,
        run_id: str,
        task_id: str,
        row: dict[str, Any],
        exc: Exception,
        location_id: int | None = None,
        mismatch: bool = False,
        started_at: str | None = None,
        content: Any | None = None,
        response: Any | None = None,
    ) -> None:
        retryable = isinstance(exc, HTTPClientError) and getattr(exc, 'retryable', False) and not isinstance(exc, (BlockedError, LocationMismatchError))
        kind = 'location_mismatch' if mismatch or isinstance(exc, LocationMismatchError) else type(exc).__name__
        request_url = row.get('canonical_url') or ''
        transport = response or getattr(exc, "http_response", None)
        http_status = getattr(transport, "status", None)
        if http_status is None:
            http_status = getattr(exc, 'http_status', None)
        response_url = getattr(transport, "url", None) or getattr(exc, 'response_url', None) or request_url
        latency_ms = getattr(transport, "elapsed_ms", None)
        if latency_ms is None:
            latency_ms = getattr(exc, 'elapsed_ms', None)
        attempt_id = self.db.record_attempt(
            task_id,
            1,
            started_at or datetime.now(timezone.utc).isoformat(),
            'error',
            request_url,
            response_url=response_url,
            http_status=http_status,
            latency_ms=latency_ms,
            requested_location=str(location_id) if location_id is not None else None,
            error_kind=kind,
            response_metadata=self._attempt_response_metadata(content=content, response=transport, exc=exc),
        )
        self.db.mark_task(task_id, 'location_mismatch' if kind == 'location_mismatch' else ('blocked' if isinstance(exc, BlockedError) else 'failed'))
        self.db.mark_failure_state(str(row['id']), location_id)
        self.db.record_error(
            run_id,
            kind,
            str(exc),
            retryable,
            task_id=task_id,
            attempt_id=attempt_id,
            product_id=str(row['id']),
            location_id=location_id,
            http_status=http_status,
            context={'url': row.get('canonical_url'), 'category': row.get('category_code'), 'traceback': traceback.format_exc()},
        )

    def crawl_products(self, category_codes: Iterable[str] | None = None, limit: int | None = None, force: bool = False, product_ids: set[str] | None = None) -> RunStats:
        self.initialize()
        codes = self._category_codes(category_codes)
        run_id = self.db.create_run('crawl products', {'categories': codes, 'limit': limit, 'force': force, 'product_ids': sorted(product_ids or [])})
        stats = RunStats(run_id=run_id)
        rows = self._rows(codes, limit, force, product_ids=product_ids)
        client = self._client()
        adapter = DMXAdapter(self.settings, client)
        try:
            for row in rows:
                task_id = self.db.create_task(run_id, 'common_product', str(row['id']), product_id=str(row['id']), url=row['canonical_url'], max_attempts=self.settings.max_attempts)
                started_at = datetime.now(timezone.utc).isoformat()
                content = None
                response = None
                try:
                    content, response = adapter.fetch_common(row['canonical_url'], row['category_code'])
                    _, changed = self.db.record_content(
                        str(row['id']),
                        content,
                        task_id=task_id,
                        response_hash=fingerprint(response.text),
                    )
                    self.db.record_attempt(
                        task_id,
                        1,
                        started_at,
                        'success',
                        row['canonical_url'],
                        response_url=response.url,
                        http_status=response.status,
                        latency_ms=response.elapsed_ms,
                        response_metadata=self._attempt_response_metadata(content=content, response=response),
                    )
                    self.db.mark_task(task_id, 'succeeded' if changed else 'unchanged')
                    stats.succeeded += int(changed)
                    stats.unchanged += int(not changed)
                except BlockedError as exc:
                    stats.blocked += 1
                    self._record_failure(
                        run_id, task_id, row, exc, started_at=started_at, content=content, response=response
                    )
                    self.db.finish_run(run_id, 'blocked', stats.as_dict(), str(exc))
                    break
                except Exception as exc:
                    stats.failed += 1
                    self._record_failure(
                        run_id, task_id, row, exc, started_at=started_at, content=content, response=response
                    )
            else:
                self.db.finish_run(run_id, 'succeeded' if stats.failed == 0 else 'partial', stats.as_dict())
            return stats
        finally:
            client.close()

    def crawl_location(self, location_code: str, category_codes: Iterable[str] | None = None, limit: int | None = None, force: bool = False, product_ids: set[str] | None = None) -> RunStats:
        self.initialize()
        location = self._location(location_code)
        codes = self._category_codes(category_codes)
        location_id = self.db.location_id(location.code)
        run_id = self.db.create_run('crawl location', {'location': location.code, 'categories': codes, 'limit': limit, 'force': force, 'product_ids': sorted(product_ids or [])})
        stats = RunStats(run_id=run_id)
        rows = self._rows(codes, limit, force, location_id=location_id, product_ids=product_ids)
        client = self._client()
        adapter = DMXAdapter(self.settings, client)
        try:
            try:
                adapter.select_location(location, verify_ward=True)
            except BlockedError as exc:
                stats.blocked = 1
                self.db.record_error(run_id, 'blocked', str(exc), False, location_id=location_id, context={'stage': 'location_select', 'location': location.code})
                self.db.finish_run(run_id, 'blocked', stats.as_dict(), str(exc))
                return stats
            except Exception as exc:
                self.db.record_error(run_id, 'location_select', str(exc), False, location_id=location_id, context={'location': location.code})
                self.db.finish_run(run_id, 'failed', stats.as_dict())
                return stats
            for row in rows:
                task_id = self.db.create_task(run_id, 'location_product', f"{row['id']}:{location.code}", product_id=str(row['id']), location_id=location_id, url=row['canonical_url'], max_attempts=self.settings.max_attempts)
                try:
                    page = adapter.fetch_product(row['canonical_url'], row['category_code'], location)
                    if page.location_snapshot is None:
                        raise LocationMismatchError('adapter returned no location snapshot')
                    content = page.content
                    snapshot = page.location_snapshot
                    raw_hash = fingerprint({'content': asdict(content), 'location': asdict(snapshot)})
                    self.db.record_attempt(task_id, 1, __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(), 'success', row['canonical_url'], response_url=row['canonical_url'])
                    _, content_changed = self.db.record_content(str(row['id']), content, task_id=task_id, response_hash=raw_hash)
                    _, location_changed = self.db.record_location(str(row['id']), location_id, snapshot, task_id=task_id, response_hash=raw_hash)
                    changed = content_changed or location_changed
                    self.db.mark_task(task_id, 'succeeded' if changed else 'unchanged')
                    stats.succeeded += int(changed)
                    stats.unchanged += int(not changed)
                except LocationMismatchError as exc:
                    stats.location_mismatch += 1
                    self._record_failure(run_id, task_id, row, exc, location_id, mismatch=True)
                except BlockedError as exc:
                    stats.blocked += 1
                    self._record_failure(run_id, task_id, row, exc, location_id)
                    self.db.finish_run(run_id, 'blocked', stats.as_dict(), str(exc))
                    break
                except Exception as exc:
                    stats.failed += 1
                    self._record_failure(run_id, task_id, row, exc, location_id)
            else:
                status = 'succeeded' if stats.failed == 0 and stats.location_mismatch == 0 else 'partial'
                self.db.finish_run(run_id, status, stats.as_dict())
            return stats
        finally:
            client.close()

    def crawl_url(self, url: str, category_codes: Iterable[str] | None = None, force: bool = True) -> RunStats:
        """Upsert and crawl one canonical URL, useful for a smoke test."""
        from urllib.parse import urlsplit
        from .models import ProductLink
        self.initialize()
        path = urlsplit(url).path.lower()
        category = next((code for code in self._category_codes(category_codes) if path.startswith('/' + code + '/')), None)
        if category is None:
            raise ValueError('cannot infer category from URL; pass --category laptop|tivi|tu-lanh')
        product_id = self.db.upsert_product(ProductLink(url=url, category_code=category, source='cli'))
        return self.crawl_products([category], limit=1, force=force, product_ids={product_id})

    def crawl_all_locations(self, category_codes: Iterable[str] | None = None, limit: int | None = None, force: bool = False) -> list[RunStats]:
        results: list[RunStats] = []
        for location in self.locations:
            if not location.active:
                continue
            result = self.crawl_location(location.code, category_codes, limit, force)
            results.append(result)
            # A challenge is host-wide; do not move on to another location
            # context after the site asks us to stop.
            if result.blocked:
                break
        return results

    def retry_errors(self, limit: int | None = None) -> list[RunStats]:
        self.initialize()
        errors = self.db.retryable_errors(limit)
        results: list[RunStats] = []
        common: dict[str, list[int]] = {}
        by_location: dict[str, dict[str, list[int]]] = {}
        for raw_error in errors:
            error = dict(raw_error)
            product_id = error.get('product_id')
            if not product_id:
                continue
            error_id = int(error['id'])
            location_code = error.get('location_code')
            if location_code:
                by_location.setdefault(str(location_code), {}).setdefault(str(product_id), []).append(error_id)
            else:
                common.setdefault(str(product_id), []).append(error_id)
        if common:
            result = self.crawl_products(force=True, product_ids=set(common))
            results.append(result)
            if result.failed == 0 and result.blocked == 0:
                for ids in common.values():
                    for error_id in ids:
                        self.db.resolve_error(error_id)
        for location, product_map in by_location.items():
            result = self.crawl_location(location, force=True, product_ids=set(product_map))
            results.append(result)
            if result.failed == 0 and result.blocked == 0 and result.location_mismatch == 0:
                for ids in product_map.values():
                    for error_id in ids:
                        self.db.resolve_error(error_id)
        return results

    def export(self, fmt: str = 'json', output: str | None = None, limit: int = 100) -> str:
        self.initialize()
        rows = self.db.export_current(limit)
        if fmt == 'json':
            text = json.dumps(rows, ensure_ascii=False, indent=2)
        elif fmt == 'csv':
            import csv
            import io
            fields = sorted({key for row in rows for key in row})
            stream = io.StringIO()
            writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
            writer.writeheader()
            for row in rows:
                writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value for key, value in row.items()})
            text = stream.getvalue()
        else:
            raise ValueError('format must be json or csv')
        if output:
            Path(output).parent.mkdir(parents=True, exist_ok=True)
            Path(output).write_text(text + ('\n' if not text.endswith('\n') else ''), encoding='utf-8')
        return text

    def doctor(self) -> dict[str, Any]:
        issues: list[str] = []
        for path in (self.settings.locations_file, self.settings.categories_file):
            if not Path(path).exists():
                issues.append(f'missing config: {path}')
        if not self.categories:
            issues.append('no active categories')
        if not self.locations:
            issues.append('no active locations')
        try:
            self.initialize()
            db_ok = True
        except Exception as exc:
            db_ok = False
            issues.append(f'database: {exc}')
        return {'ok': not issues, 'database': self.settings.database_url, 'categories': [c.code for c in self.categories], 'locations': [l.code for l in self.locations], 'issues': issues, 'db_initialized': db_ok}
