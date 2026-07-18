from __future__ import annotations

import os
import unittest
import uuid
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit, urlunsplit

from dmx_crawler.config import Settings
from dmx_crawler.crawler import Crawler
from dmx_crawler.db import Database
from dmx_crawler.http import HTTPResponse
from dmx_crawler.models import CategoryConfig, ProductContent


ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS = (
    ROOT / "migrations" / "001_initial.sql",
    ROOT / "migrations" / "002_rich_product_spec_values.sql",
    ROOT / "migrations" / "003_split_catalog_crawler_schemas.sql",
)

CATALOG_TABLES = (
    "categories",
    "locations",
    "media_assets",
    "product_content_versions",
    "product_location_versions",
    "product_spec_values",
    "product_version_media",
    "products",
    "spec_definitions",
)
CRAWLER_TABLES = (
    "crawl_attempts",
    "crawl_errors",
    "crawl_observations",
    "crawl_runs",
    "crawl_tasks",
    "discovery_sources",
    "product_crawl_state",
    "product_location_crawl_state",
    "product_urls",
)
ALL_TABLES = tuple(sorted(CATALOG_TABLES + CRAWLER_TABLES))
TABLE_SCHEMA = {
    **{table: "catalog" for table in CATALOG_TABLES},
    **{table: "crawler" for table in CRAWLER_TABLES},
}

LEGACY_RUN_ID = "00000000-0000-0000-0000-000000000001"
LEGACY_PRODUCT_ID = "00000000-0000-0000-0000-000000000101"
LEGACY_TASK_ID = "00000000-0000-0000-0000-000000000201"
LEGACY_CONTENT_ID = "00000000-0000-0000-0000-000000000301"
LEGACY_MEDIA_ID = "00000000-0000-0000-0000-000000000401"
LEGACY_LOCATION_VERSION_ID = "00000000-0000-0000-0000-000000000501"


class _NoNetworkClient:
    def close(self) -> None:
        pass


class _SyntheticAdapter:
    """Offline adapter whose A/A/B queue is supplied by the test."""

    contents: list[ProductContent] = []
    bodies: list[bytes] = []

    def __init__(self, settings: Settings, client: _NoNetworkClient):
        self.settings = settings
        self.client = client

    def fetch_common(self, url: str, category_code: str) -> tuple[ProductContent, HTTPResponse]:
        content = self.contents.pop(0)
        body = self.bodies.pop(0)
        return content, HTTPResponse(
            status=200,
            url=url,
            headers={"content-type": "text/html; charset=utf-8"},
            body=body,
            elapsed_ms=1,
            attempts=1,
        )


def _synthetic_content(*, ram: str, sold_count: int) -> ProductContent:
    url = "https://example.invalid/laptop/schema-split-product"
    items = [
        {
            "group": "Bộ xử lý",
            "group_ordinal": 0,
            "label": "Công nghệ CPU",
            "raw_label": "Công nghệ CPU",
            "value": "Synthetic CPU",
            "raw_value": "Synthetic CPU",
            "value_text": "Synthetic CPU",
            "item_ordinal": 0,
            "source": "dom",
            "provenance": ["dom"],
        },
        {
            "group": "Bộ nhớ",
            "group_ordinal": 1,
            "label": "RAM",
            "raw_label": "RAM",
            "value": ram,
            "raw_value": ram,
            "value_text": ram,
            "item_ordinal": 0,
            "source": "dom",
            "provenance": ["dom"],
        },
    ]
    groups = [
        {
            "group": "Bộ xử lý",
            "ordinal": 0,
            "items": [dict(items[0], ordinal=0)],
        },
        {
            "group": "Bộ nhớ",
            "ordinal": 1,
            "items": [dict(items[1], ordinal=0)],
        },
    ]
    return ProductContent(
        canonical_url=url,
        category_code="laptop",
        name="Laptop Synthetic Schema Split",
        brand="Synthetic",
        model="SCHEMA-SPLIT-1",
        source_product_key="schema-split-source-key",
        product_code="SCHEMA-SPLIT-1",
        rating=4.5,
        rating_count=10,
        sold_count=sold_count,
        specs=items,
        specs_raw=groups,
        specs_diagnostics={
            "group_count": 2,
            "total_item_count": 2,
            "empty_groups": [],
            "warnings": [],
        },
        images=["https://example.invalid/assets/schema-split-product.jpg"],
        stock_status="in_stock",
        stock_raw="Còn hàng",
    )


class PostgreSQLSchemaSplitIntegrationTests(unittest.TestCase):
    """Opt-in tests; every case owns and removes a uniquely named database."""

    @classmethod
    def setUpClass(cls) -> None:
        admin_url = os.environ.get("DMX_TEST_POSTGRES_ADMIN_URL")
        if not admin_url:
            raise unittest.SkipTest(
                "set DMX_TEST_POSTGRES_ADMIN_URL to a dedicated local PostgreSQL admin URL"
            )
        parsed = urlsplit(admin_url)
        if parsed.scheme not in {"postgres", "postgresql"}:
            raise RuntimeError("DMX_TEST_POSTGRES_ADMIN_URL must be a PostgreSQL URL")
        if parsed.hostname not in {None, "localhost", "127.0.0.1", "::1"}:
            raise RuntimeError(
                "DMX_TEST_POSTGRES_ADMIN_URL must use localhost or a local Unix socket"
            )
        try:
            import psycopg
            from psycopg import sql
            from psycopg.rows import dict_row
        except ImportError as error:
            raise RuntimeError(
                "DMX_TEST_POSTGRES_ADMIN_URL is set but psycopg is not installed"
            ) from error

        cls.admin_url = admin_url
        cls.parsed_admin_url = parsed
        cls.psycopg = psycopg
        cls.sql = sql
        cls.dict_row = staticmethod(dict_row)

    def setUp(self) -> None:
        self.database_name = f"dmx_schema_split_test_{uuid.uuid4().hex}"
        self.role_names: list[str] = []
        self.database_objects: list[Database] = []
        self.admin = self.psycopg.connect(self.admin_url, autocommit=True)
        self.admin.execute(
            self.sql.SQL("CREATE DATABASE {}").format(
                self.sql.Identifier(self.database_name)
            )
        )
        self.database_url = urlunsplit(
            self.parsed_admin_url._replace(path=f"/{self.database_name}")
        )
        try:
            self.conn = self.psycopg.connect(
                self.database_url,
                autocommit=True,
                row_factory=self.dict_row,
            )
        except Exception:
            self.admin.execute(
                self.sql.SQL("DROP DATABASE {} WITH (FORCE)").format(
                    self.sql.Identifier(self.database_name)
                )
            )
            self.admin.close()
            raise

    def tearDown(self) -> None:
        for database in reversed(self.database_objects):
            try:
                database.close()
            except Exception:
                pass
        try:
            self.conn.close()
        finally:
            self.admin.execute(
                self.sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                    self.sql.Identifier(self.database_name)
                )
            )
            for role_name in reversed(self.role_names):
                self.admin.execute(
                    self.sql.SQL("DROP ROLE IF EXISTS {}").format(
                        self.sql.Identifier(role_name)
                    )
                )
            self.admin.close()

    def _apply_migration(self, index: int) -> None:
        migration = MIGRATIONS[index]
        self.assertTrue(migration.is_file(), f"missing migration: {migration.name}")
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(migration.read_text(encoding="utf-8"), prepare=False)
        except Exception:
            self.conn.rollback()
            raise

    def _apply_legacy_schema(self) -> None:
        self._apply_migration(0)
        self._apply_migration(1)

    def _rows(self, query: object, params: tuple[object, ...] = ()) -> list[dict[str, object]]:
        return list(self.conn.execute(query, params).fetchall())

    def _row(self, query: object, params: tuple[object, ...] = ()) -> dict[str, object]:
        row = self.conn.execute(query, params).fetchone()
        self.assertIsNotNone(row)
        return row

    def _scalar(self, query: object, params: tuple[object, ...] = ()) -> object:
        row = self.conn.execute(query, params).fetchone()
        self.assertIsNotNone(row)
        return next(iter(row.values()))

    def _table_oids(self, schemas: tuple[str, ...]) -> dict[str, int]:
        rows = self._rows(
            """
            SELECT c.relname AS table_name, c.oid::bigint AS table_oid
              FROM pg_catalog.pg_class AS c
              JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
             WHERE c.relkind IN ('r', 'p')
               AND n.nspname = ANY(%s)
               AND c.relname = ANY(%s)
             ORDER BY c.relname
            """,
            (list(schemas), list(ALL_TABLES)),
        )
        self.assertEqual(
            len(rows),
            len({str(row["table_name"]) for row in rows}),
            "an allow-listed table exists in more than one inspected schema",
        )
        return {
            str(row["table_name"]): int(row["table_oid"])
            for row in rows
        }

    def _placement(self) -> set[tuple[str, str]]:
        return {
            (str(row["schema_name"]), str(row["table_name"]))
            for row in self._rows(
                """
                SELECT n.nspname AS schema_name, c.relname AS table_name
                  FROM pg_catalog.pg_class AS c
                  JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
                 WHERE c.relkind IN ('r', 'p')
                   AND n.nspname IN ('public', 'catalog', 'crawler')
                   AND c.relname = ANY(%s)
                 ORDER BY n.nspname, c.relname
                """,
                (list(ALL_TABLES),),
            )
        }

    def _structural_metadata(self, table_oids: dict[str, int]) -> dict[str, object]:
        oids = list(table_oids.values())
        constraints = self._rows(
            """
            SELECT con.oid::bigint AS constraint_oid,
                   con.conname,
                   con.contype,
                   con.conbin::text AS expression_tree,
                   regexp_replace(
                       pg_catalog.pg_get_constraintdef(con.oid, true),
                       '(public|catalog|crawler)[.]', '', 'g'
                   ) AS definition,
                   con.conrelid::bigint AS table_oid,
                   con.confrelid::bigint AS referenced_table_oid,
                   con.conkey::text AS constrained_columns,
                   con.confkey::text AS referenced_columns,
                   con.confupdtype,
                   con.confdeltype,
                   con.confmatchtype,
                   con.condeferrable,
                   con.condeferred,
                   con.convalidated
              FROM pg_catalog.pg_constraint AS con
             WHERE con.conrelid = ANY(%s)
             ORDER BY con.oid
            """,
            (oids,),
        )
        indexes = self._rows(
            """
            SELECT idx.oid::bigint AS index_oid,
                   idx.relname AS index_name,
                   regexp_replace(
                       pg_catalog.pg_get_indexdef(idx.oid),
                       '(public|catalog|crawler)[.]', '', 'g'
                   ) AS definition,
                   ind.indrelid::bigint AS table_oid,
                   ind.indisunique,
                   ind.indisprimary,
                   ind.indisexclusion,
                   ind.indimmediate,
                   ind.indisclustered,
                   ind.indisvalid,
                   ind.indisready,
                   ind.indislive,
                   ind.indkey::text AS indexed_columns,
                   ind.indclass::text AS operator_classes,
                   ind.indcollation::text AS collations,
                   ind.indoption::text AS options,
                   pg_catalog.pg_get_expr(ind.indexprs, ind.indrelid, true) AS expression,
                   pg_catalog.pg_get_expr(ind.indpred, ind.indrelid, true) AS predicate
              FROM pg_catalog.pg_index AS ind
              JOIN pg_catalog.pg_class AS idx ON idx.oid = ind.indexrelid
             WHERE ind.indrelid = ANY(%s)
             ORDER BY idx.oid
            """,
            (oids,),
        )
        sequences = self._rows(
            """
            SELECT seq.oid::bigint AS sequence_oid,
                   seq.relname AS sequence_name,
                   dep.refobjid::bigint AS table_oid,
                   dep.refobjsubid AS column_number,
                   attr.attname AS column_name,
                   def.oid::bigint AS default_oid,
                   sequence_options.seqtypid::regtype::text AS data_type,
                   sequence_options.seqstart,
                   sequence_options.seqincrement,
                   sequence_options.seqmax,
                   sequence_options.seqmin,
                   sequence_options.seqcache,
                   sequence_options.seqcycle
              FROM pg_catalog.pg_class AS seq
              JOIN pg_catalog.pg_depend AS dep
                ON dep.classid = 'pg_catalog.pg_class'::regclass
               AND dep.objid = seq.oid
               AND dep.refclassid = 'pg_catalog.pg_class'::regclass
               AND dep.deptype = 'a'
              JOIN pg_catalog.pg_attribute AS attr
                ON attr.attrelid = dep.refobjid
               AND attr.attnum = dep.refobjsubid
              LEFT JOIN pg_catalog.pg_attrdef AS def
                ON def.adrelid = dep.refobjid
               AND def.adnum = dep.refobjsubid
              JOIN pg_catalog.pg_sequence AS sequence_options
                ON sequence_options.seqrelid = seq.oid
             WHERE seq.relkind = 'S'
               AND dep.refobjid = ANY(%s)
             ORDER BY seq.oid
            """,
            (oids,),
        )
        return {
            "table_oids": table_oids,
            "constraints": constraints,
            "indexes": indexes,
            "sequences": sequences,
        }

    def _sequence_details(self, table_oids: dict[str, int]) -> list[dict[str, object]]:
        return self._rows(
            """
            SELECT seq.oid::bigint AS sequence_oid,
                   seq_ns.nspname AS sequence_schema,
                   seq.relname AS sequence_name,
                   tbl.oid::bigint AS table_oid,
                   tbl_ns.nspname AS table_schema,
                   tbl.relname AS table_name,
                   attr.attname AS column_name,
                   def.oid::bigint AS default_oid,
                   pg_catalog.pg_get_expr(def.adbin, def.adrelid) AS column_default
              FROM pg_catalog.pg_class AS seq
              JOIN pg_catalog.pg_namespace AS seq_ns ON seq_ns.oid = seq.relnamespace
              JOIN pg_catalog.pg_depend AS dep
                ON dep.classid = 'pg_catalog.pg_class'::regclass
               AND dep.objid = seq.oid
               AND dep.refclassid = 'pg_catalog.pg_class'::regclass
               AND dep.deptype = 'a'
              JOIN pg_catalog.pg_class AS tbl ON tbl.oid = dep.refobjid
              JOIN pg_catalog.pg_namespace AS tbl_ns ON tbl_ns.oid = tbl.relnamespace
              JOIN pg_catalog.pg_attribute AS attr
                ON attr.attrelid = dep.refobjid
               AND attr.attnum = dep.refobjsubid
              JOIN pg_catalog.pg_attrdef AS def
                ON def.adrelid = dep.refobjid
               AND def.adnum = dep.refobjsubid
             WHERE seq.relkind = 'S'
               AND tbl.oid = ANY(%s)
             ORDER BY seq.oid
            """,
            (list(table_oids.values()),),
        )

    def _sequence_state(
        self, details: list[dict[str, object]]
    ) -> dict[str, tuple[int, bool]]:
        result: dict[str, tuple[int, bool]] = {}
        for detail in details:
            row = self._row(
                self.sql.SQL(
                    "SELECT last_value::bigint AS last_value, is_called FROM {}.{}"
                ).format(
                    self.sql.Identifier(str(detail["sequence_schema"])),
                    self.sql.Identifier(str(detail["sequence_name"])),
                )
            )
            result[str(detail["sequence_name"])] = (
                int(row["last_value"]),
                bool(row["is_called"]),
            )
        return result

    def _data_snapshot(self, schema_by_table: dict[str, str]) -> dict[str, str]:
        snapshot: dict[str, str] = {}
        for table in ALL_TABLES:
            query = self.sql.SQL(
                """
                SELECT COALESCE(
                    jsonb_agg(to_jsonb(source_row)
                              ORDER BY to_jsonb(source_row)::text),
                    '[]'::jsonb
                )::text AS payload
                  FROM {}.{} AS source_row
                """
            ).format(
                self.sql.Identifier(schema_by_table[table]),
                self.sql.Identifier(table),
            )
            snapshot[table] = str(self._scalar(query))
        return snapshot

    def _seed_every_legacy_table(self) -> None:
        self.conn.execute(
            f"""
            INSERT INTO public.categories(code, name)
            VALUES ('legacy-category', 'Legacy Category');

            INSERT INTO public.locations(
                code, name, province_id, province_name, ward_id, ward_name,
                address, config_hash
            )
            VALUES (
                'legacy-location', 'Legacy Location', 1, 'Synthetic Province',
                2, 'Synthetic Ward', '', repeat('a', 64)
            );

            INSERT INTO public.crawl_runs(
                id, command, mode, status, started_at
            )
            VALUES (
                '{LEGACY_RUN_ID}', 'legacy seed', 'test', 'running',
                '2026-01-01T00:00:00+00:00'
            );

            INSERT INTO public.products(
                id, source, source_product_key, canonical_url,
                canonical_url_hash, category_id, status, first_seen_at,
                last_seen_at
            )
            SELECT
                '{LEGACY_PRODUCT_ID}', 'fixture', 'legacy-product',
                'https://example.invalid/legacy-product', repeat('b', 64), id,
                'active', '2026-01-01T00:00:00+00:00',
                '2026-01-01T00:00:00+00:00'
              FROM public.categories
             WHERE code = 'legacy-category';

            INSERT INTO public.product_urls(
                product_id, source, url, url_hash, first_seen_at, last_seen_at
            )
            VALUES (
                '{LEGACY_PRODUCT_ID}', 'fixture',
                'https://example.invalid/legacy-product', repeat('c', 64),
                '2026-01-01T00:00:00+00:00',
                '2026-01-01T00:00:00+00:00'
            );

            INSERT INTO public.crawl_tasks(
                id, run_id, task_type, target_key, product_id, location_id,
                url, status, available_at, created_at
            )
            SELECT
                '{LEGACY_TASK_ID}', '{LEGACY_RUN_ID}', 'common_product',
                'legacy-product', '{LEGACY_PRODUCT_ID}', id,
                'https://example.invalid/legacy-product', 'succeeded',
                '2026-01-01T00:00:00+00:00',
                '2026-01-01T00:00:00+00:00'
              FROM public.locations
             WHERE code = 'legacy-location';

            INSERT INTO public.crawl_attempts(
                task_id, attempt_no, started_at, finished_at, http_status,
                request_url, response_url, outcome
            )
            VALUES (
                '{LEGACY_TASK_ID}', 1, '2026-01-01T00:00:00+00:00',
                '2026-01-01T00:00:01+00:00', 200,
                'https://example.invalid/legacy-product',
                'https://example.invalid/legacy-product', 'success'
            );

            INSERT INTO public.product_content_versions(
                id, product_id, category_id, name, specs_raw_json,
                content_hash, valid_from, created_by_task_id
            )
            SELECT
                '{LEGACY_CONTENT_ID}', '{LEGACY_PRODUCT_ID}', id,
                'Legacy Product', '[]'::jsonb, repeat('d', 64),
                '2026-01-01T00:00:00+00:00', '{LEGACY_TASK_ID}'
              FROM public.categories
             WHERE code = 'legacy-category';

            INSERT INTO public.spec_definitions(
                category_id, normalized_key, canonical_label
            )
            SELECT id, 'legacy_spec', 'Legacy Spec'
              FROM public.categories
             WHERE code = 'legacy-category';

            INSERT INTO public.product_spec_values(
                content_version_id, definition_id, group_name, raw_label,
                raw_value, value_text
            )
            SELECT
                '{LEGACY_CONTENT_ID}', id, 'Legacy Group', 'Legacy Spec',
                'Legacy Value', 'Legacy Value'
              FROM public.spec_definitions
             WHERE normalized_key = 'legacy_spec';

            INSERT INTO public.media_assets(id, url, url_hash)
            VALUES (
                '{LEGACY_MEDIA_ID}',
                'https://example.invalid/assets/legacy.jpg', repeat('e', 64)
            );

            INSERT INTO public.product_version_media(
                content_version_id, media_id, role
            )
            VALUES ('{LEGACY_CONTENT_ID}', '{LEGACY_MEDIA_ID}', 'primary');

            INSERT INTO public.product_location_versions(
                id, product_id, location_id, sale_price, state_hash,
                valid_from, created_by_task_id
            )
            SELECT
                '{LEGACY_LOCATION_VERSION_ID}', '{LEGACY_PRODUCT_ID}', id,
                1000000, repeat('f', 64),
                '2026-01-01T00:00:00+00:00', '{LEGACY_TASK_ID}'
              FROM public.locations
             WHERE code = 'legacy-location';

            INSERT INTO public.crawl_observations(
                task_id, product_id, location_id, content_version_id,
                location_version_id, changed, observed_at, response_hash
            )
            SELECT
                '{LEGACY_TASK_ID}', '{LEGACY_PRODUCT_ID}', id,
                '{LEGACY_CONTENT_ID}', '{LEGACY_LOCATION_VERSION_ID}', true,
                '2026-01-01T00:00:00+00:00', repeat('1', 64)
              FROM public.locations
             WHERE code = 'legacy-location';

            INSERT INTO public.product_crawl_state(
                product_id, last_attempt_at, last_success_at,
                consecutive_unchanged, failure_streak
            )
            VALUES (
                '{LEGACY_PRODUCT_ID}', '2026-01-01T00:00:00+00:00',
                '2026-01-01T00:00:00+00:00', 0, 0
            );

            INSERT INTO public.product_location_crawl_state(
                product_id, location_id, last_attempt_at, last_success_at,
                consecutive_unchanged, failure_streak
            )
            SELECT
                '{LEGACY_PRODUCT_ID}', id, '2026-01-01T00:00:00+00:00',
                '2026-01-01T00:00:00+00:00', 0, 0
              FROM public.locations
             WHERE code = 'legacy-location';

            INSERT INTO public.discovery_sources(url, source_type)
            VALUES ('https://example.invalid/legacy-source', 'fixture');

            INSERT INTO public.crawl_errors(
                run_id, task_id, attempt_id, product_id, location_id,
                error_kind, message, retryable, created_at
            )
            SELECT
                '{LEGACY_RUN_ID}', '{LEGACY_TASK_ID}', attempt.id,
                '{LEGACY_PRODUCT_ID}', location.id, 'legacy_fixture',
                'synthetic legacy fixture', false,
                '2026-01-01T00:00:00+00:00'
              FROM public.crawl_attempts AS attempt
              CROSS JOIN public.locations AS location
             WHERE attempt.task_id = '{LEGACY_TASK_ID}'
               AND location.code = 'legacy-location';
            """,
            prepare=False,
        )

    def _assert_sequence_placement_and_defaults(
        self, details: list[dict[str, object]]
    ) -> None:
        self.assertEqual(len(details), 8)
        for detail in details:
            table_name = str(detail["table_name"])
            expected_schema = TABLE_SCHEMA[table_name]
            self.assertEqual(detail["table_schema"], expected_schema)
            self.assertEqual(detail["sequence_schema"], expected_schema)
            sequence_name = str(detail["sequence_name"])
            self.assertIn(
                f"{expected_schema}.{sequence_name}",
                str(detail["column_default"]),
            )
            serial_sequence = self._scalar(
                "SELECT pg_catalog.pg_get_serial_sequence(%s, %s) AS sequence_name",
                (f"{expected_schema}.{table_name}", str(detail["column_name"])),
            )
            self.assertEqual(
                serial_sequence,
                f"{expected_schema}.{sequence_name}",
            )

    def _assert_serial_inserts_work(self) -> None:
        statements = (
            """
            INSERT INTO catalog.categories(code, name)
            VALUES ('sequence-category', 'Sequence Category')
            RETURNING id
            """,
            """
            INSERT INTO catalog.locations(
                code, name, province_id, province_name, ward_id, ward_name,
                address, config_hash
            )
            VALUES (
                'sequence-location', 'Sequence Location', 10,
                'Synthetic Province', 11, 'Synthetic Ward', '',
                repeat('2', 64)
            )
            RETURNING id
            """,
            f"""
            INSERT INTO crawler.product_urls(
                product_id, source, url, url_hash, first_seen_at, last_seen_at
            )
            VALUES (
                '{LEGACY_PRODUCT_ID}', 'fixture',
                'https://example.invalid/sequence-url', repeat('3', 64),
                '2026-01-02T00:00:00+00:00',
                '2026-01-02T00:00:00+00:00'
            )
            RETURNING id
            """,
            """
            INSERT INTO crawler.crawl_attempts(
                attempt_no, started_at, outcome
            )
            VALUES (1, '2026-01-02T00:00:00+00:00', 'fixture')
            RETURNING id
            """,
            """
            INSERT INTO crawler.crawl_errors(
                error_kind, message, retryable, created_at
            )
            VALUES (
                'sequence_fixture', 'synthetic fixture', false,
                '2026-01-02T00:00:00+00:00'
            )
            RETURNING id
            """,
            """
            INSERT INTO catalog.spec_definitions(
                category_id, normalized_key, canonical_label
            )
            SELECT id, 'sequence_spec', 'Sequence Spec'
              FROM catalog.categories
             WHERE code = 'legacy-category'
            RETURNING id
            """,
            f"""
            INSERT INTO catalog.product_spec_values(
                content_version_id, group_name, raw_label, raw_value,
                value_text
            )
            VALUES (
                '{LEGACY_CONTENT_ID}', 'Sequence Group', 'Sequence Spec',
                'Sequence Value', 'Sequence Value'
            )
            RETURNING id
            """,
            f"""
            INSERT INTO crawler.crawl_observations(
                product_id, changed, observed_at
            )
            VALUES (
                '{LEGACY_PRODUCT_ID}', false,
                '2026-01-02T00:00:00+00:00'
            )
            RETURNING id
            """,
        )
        generated_ids = [int(self._scalar(statement)) for statement in statements]
        self.assertEqual(len(generated_ids), 8)
        self.assertTrue(all(value > 0 for value in generated_ids))

    def _exercise_synthetic_crawler(self) -> str:
        url = "https://example.invalid/laptop/schema-split-product"
        content_a = _synthetic_content(ram="8 GB", sold_count=10)
        content_b = replace(
            _synthetic_content(ram="16 GB", sold_count=11),
            description="Synthetic changed content",
        )
        _SyntheticAdapter.contents = [content_a, content_a, content_b]
        _SyntheticAdapter.bodies = [b"synthetic-a", b"synthetic-a", b"synthetic-b"]

        database = Database(self.database_url)
        self.database_objects.append(database)
        crawler = Crawler(
            settings=Settings(
                database_url=self.database_url,
                min_request_interval_seconds=0,
                max_attempts=1,
            ),
            db=database,
            categories=[
                CategoryConfig(
                    code="laptop",
                    name="Laptop",
                    url="https://example.invalid/laptop",
                    path_prefix="/laptop/",
                )
            ],
            locations=[],
        )
        with patch("dmx_crawler.crawler.DMXAdapter", _SyntheticAdapter), patch.object(
            crawler, "_client", return_value=_NoNetworkClient()
        ):
            stats = [
                crawler.crawl_url(url, ["laptop"]),
                crawler.crawl_url(url, ["laptop"]),
                crawler.crawl_url(url, ["laptop"]),
            ]

        self.assertEqual(
            [(item.succeeded, item.unchanged, item.failed) for item in stats],
            [(1, 0, 0), (0, 1, 0), (1, 0, 0)],
        )
        product = self._row(
            """
            SELECT id
              FROM catalog.products
             WHERE canonical_url = %s
            """,
            (url,),
        )
        product_id = str(product["id"])
        versions = self._rows(
            """
            SELECT id::text AS id, content_hash, valid_to
              FROM catalog.product_content_versions
             WHERE product_id = %s
             ORDER BY valid_from, id
            """,
            (product_id,),
        )
        self.assertEqual(len(versions), 2)
        self.assertEqual(sum(row["valid_to"] is None for row in versions), 1)
        self.assertEqual(sum(row["valid_to"] is not None for row in versions), 1)
        self.assertNotEqual(versions[0]["content_hash"], versions[1]["content_hash"])

        specs_by_version = self._rows(
            """
            SELECT content_version_id::text AS content_version_id,
                   count(*)::int AS spec_count
              FROM catalog.product_spec_values
             WHERE content_version_id = ANY(%s::uuid[])
             GROUP BY content_version_id
             ORDER BY content_version_id
            """,
            ([str(row["id"]) for row in versions],),
        )
        self.assertEqual(
            sorted(int(row["spec_count"]) for row in specs_by_version),
            [2, 2],
        )
        self.assertEqual(
            int(
                self._scalar(
                    """
                    SELECT count(*)::int
                      FROM catalog.product_spec_values
                     WHERE content_version_id = ANY(%s::uuid[])
                    """,
                    ([str(row["id"]) for row in versions],),
                )
            ),
            4,
        )

        operational = self._row(
            """
            SELECT
                (SELECT count(*)::int
                   FROM crawler.crawl_runs
                  WHERE arguments_json->'product_ids' @> to_jsonb(%s::text)) AS runs,
                (SELECT count(*)::int
                   FROM crawler.crawl_tasks
                  WHERE product_id = %s) AS tasks,
                (SELECT count(*)::int
                   FROM crawler.crawl_attempts AS attempt
                   JOIN crawler.crawl_tasks AS task ON task.id = attempt.task_id
                  WHERE task.product_id = %s) AS attempts,
                (SELECT count(*)::int
                   FROM crawler.crawl_observations
                  WHERE product_id = %s) AS observations
            """,
            (product_id, product_id, product_id, product_id),
        )
        self.assertEqual(
            (
                int(operational["runs"]),
                int(operational["tasks"]),
                int(operational["attempts"]),
                int(operational["observations"]),
            ),
            (3, 3, 3, 3),
        )
        observation_changes = [
            bool(row["changed"])
            for row in self._rows(
                """
                SELECT changed
                  FROM crawler.crawl_observations
                 WHERE product_id = %s
                 ORDER BY id
                """,
                (product_id,),
            )
        ]
        self.assertEqual(observation_changes, [True, False, True])
        state = self._row(
            """
            SELECT consecutive_unchanged, failure_streak, last_success_at
              FROM crawler.product_crawl_state
             WHERE product_id = %s
            """,
            (product_id,),
        )
        self.assertEqual(
            (int(state["consecutive_unchanged"]), int(state["failure_streak"])),
            (0, 0),
        )
        self.assertIsNotNone(state["last_success_at"])
        attempt_ids = [
            int(row["id"])
            for row in self._rows(
                """
                SELECT attempt.id
                  FROM crawler.crawl_attempts AS attempt
                  JOIN crawler.crawl_tasks AS task ON task.id = attempt.task_id
                 WHERE task.product_id = %s
                 ORDER BY attempt.id
                """,
                (product_id,),
            )
        ]
        self.assertEqual(len(attempt_ids), 3)
        self.assertTrue(all(attempt_id > 0 for attempt_id in attempt_ids))
        return product_id

    def _assert_catalog_only_export(self, product_id: str) -> None:
        role_name = f"dmx_catalog_reader_{uuid.uuid4().hex}"
        self.role_names.append(role_name)
        identifier = self.sql.Identifier(role_name)
        self.conn.execute(
            self.sql.SQL("CREATE ROLE {} NOLOGIN").format(identifier)
        )
        self.conn.execute(
            self.sql.SQL("GRANT USAGE ON SCHEMA catalog TO {}").format(identifier)
        )
        self.conn.execute(
            self.sql.SQL(
                "GRANT SELECT ON ALL TABLES IN SCHEMA catalog TO {}"
            ).format(identifier)
        )

        privileges = self._row(
            """
            SELECT
                pg_catalog.has_schema_privilege(%s, 'catalog', 'USAGE') AS catalog_usage,
                pg_catalog.has_schema_privilege(%s, 'crawler', 'USAGE') AS crawler_usage
            """,
            (role_name, role_name),
        )
        self.assertTrue(privileges["catalog_usage"])
        self.assertFalse(privileges["crawler_usage"])

        restricted = Database(self.database_url)
        self.database_objects.append(restricted)
        restricted.conn.execute(
            self.sql.SQL("SET ROLE {}").format(identifier)
        )
        exported = restricted.export_current(limit=100)
        self.assertIn(
            product_id,
            {str(item["id"]) for item in exported},
        )
        with self.assertRaises(self.psycopg.errors.InsufficientPrivilege):
            restricted.execute("SELECT id FROM crawler.crawl_runs LIMIT 1")
        restricted.conn.rollback()
        restricted.conn.execute("RESET ROLE")
        restricted.conn.commit()

    def test_split_preserves_metadata_data_and_supports_runtime(self) -> None:
        self._apply_legacy_schema()
        self.conn.execute(
            """
            CREATE TABLE public.unrelated_fixture (
                id integer PRIMARY KEY,
                note text NOT NULL
            );
            INSERT INTO public.unrelated_fixture(id, note)
            VALUES (1, 'must remain in public');
            """,
            prepare=False,
        )
        self._seed_every_legacy_table()

        before_oids = self._table_oids(("public",))
        self.assertEqual(set(before_oids), set(ALL_TABLES))
        before_metadata = self._structural_metadata(before_oids)
        before_data = self._data_snapshot(
            {table: "public" for table in ALL_TABLES}
        )
        before_sequence_details = self._sequence_details(before_oids)
        before_sequence_state = self._sequence_state(before_sequence_details)
        constraint_types = {
            constraint_type: sum(
                row["contype"] == constraint_type
                for row in before_metadata["constraints"]
            )
            for constraint_type in ("p", "f", "u", "c")
        }
        self.assertEqual(
            constraint_types,
            {"p": 18, "f": 32, "u": 7, "c": 3},
        )
        self.assertEqual(len(before_metadata["indexes"]), 33)
        self.assertEqual(len(before_metadata["sequences"]), 8)

        self._apply_migration(2)

        expected_placement = {
            *((("catalog", table) for table in CATALOG_TABLES)),
            *((("crawler", table) for table in CRAWLER_TABLES)),
        }
        self.assertEqual(self._placement(), expected_placement)
        after_first_oids = self._table_oids(("catalog", "crawler"))
        after_first_metadata = self._structural_metadata(after_first_oids)
        after_first_data = self._data_snapshot(TABLE_SCHEMA)
        after_first_sequence_details = self._sequence_details(after_first_oids)
        after_first_sequence_state = self._sequence_state(
            after_first_sequence_details
        )
        self.assertEqual(after_first_oids, before_oids)
        self.assertEqual(after_first_metadata, before_metadata)
        self.assertEqual(after_first_data, before_data)
        self.assertEqual(after_first_sequence_state, before_sequence_state)
        self._assert_sequence_placement_and_defaults(after_first_sequence_details)
        unrelated = self._row(
            "SELECT id, note FROM public.unrelated_fixture"
        )
        self.assertEqual(
            (int(unrelated["id"]), unrelated["note"]),
            (1, "must remain in public"),
        )

        self._apply_migration(2)

        after_second_oids = self._table_oids(("catalog", "crawler"))
        after_second_metadata = self._structural_metadata(after_second_oids)
        after_second_data = self._data_snapshot(TABLE_SCHEMA)
        after_second_sequence_details = self._sequence_details(after_second_oids)
        after_second_sequence_state = self._sequence_state(
            after_second_sequence_details
        )
        self.assertEqual(self._placement(), expected_placement)
        self.assertEqual(after_second_oids, after_first_oids)
        self.assertEqual(after_second_metadata, after_first_metadata)
        self.assertEqual(after_second_data, after_first_data)
        self.assertEqual(after_second_sequence_state, after_first_sequence_state)
        self.assertEqual(after_second_sequence_details, after_first_sequence_details)
        self._assert_sequence_placement_and_defaults(after_second_sequence_details)

        self._assert_serial_inserts_work()
        product_id = self._exercise_synthetic_crawler()
        self._assert_catalog_only_export(product_id)

    def test_partial_split_is_rejected_and_initialize_fails_fast(self) -> None:
        self._apply_legacy_schema()
        self.conn.execute("CREATE SCHEMA catalog")
        self.conn.execute("CREATE SCHEMA crawler")
        self.conn.execute(
            "ALTER TABLE public.categories SET SCHEMA catalog"
        )
        before = self._placement()

        with self.assertRaises(self.psycopg.Error) as caught:
            self._apply_migration(2)
        self.assertIn("categories", str(caught.exception).casefold())
        self.assertEqual(self._placement(), before)

        database = Database(self.database_url)
        self.database_objects.append(database)
        with self.assertRaises(RuntimeError):
            database.initialize()


    def test_missing_allow_listed_table_is_rejected_without_side_effects(self) -> None:
        self._apply_legacy_schema()
        self.conn.execute("DROP TABLE public.discovery_sources")
        before = self._placement()

        with self.assertRaises(self.psycopg.Error) as caught:
            self._apply_migration(2)
        self.assertIn("discovery_sources", str(caught.exception).casefold())
        self.assertEqual(self._placement(), before)


if __name__ == "__main__":
    unittest.main()
