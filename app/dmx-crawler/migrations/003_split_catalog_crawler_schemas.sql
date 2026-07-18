-- Split the existing PostgreSQL tables into product-facing and crawler-facing
-- schemas without copying data or recreating database objects.
--
-- Supported starting states:
--   1. All 18 application tables are in public and none of their names exist
--      in catalog/crawler. The tables are moved in place.
--   2. All 18 application tables are already in their intended schemas and
--      none remain in public. The migration validates the split and is a no-op.
-- Any missing, duplicated, misplaced, or partially moved application table
-- aborts the transaction. Relations outside the explicit allow-list below are
-- deliberately ignored.
--
-- ALTER TABLE ... SET SCHEMA preserves table identity and moves associated
-- indexes, constraints, and owned sequences. The postconditions below verify
-- those properties. Schema privileges are deployment concerns: this migration
-- intentionally does not grant privileges to any hard-coded role.

BEGIN;

CREATE TEMP TABLE _dmx_003_table_snapshot (
    table_name TEXT PRIMARY KEY,
    target_schema TEXT NOT NULL,
    table_oid OID NOT NULL UNIQUE
) ON COMMIT DROP;

CREATE TEMP TABLE _dmx_003_constraint_snapshot (
    constraint_oid OID PRIMARY KEY,
    constraint_name TEXT NOT NULL,
    table_oid OID NOT NULL,
    referenced_table_oid OID NOT NULL,
    constraint_type "char" NOT NULL,
    is_validated BOOLEAN NOT NULL,
    is_deferrable BOOLEAN NOT NULL,
    is_deferred BOOLEAN NOT NULL,
    update_action "char" NOT NULL,
    delete_action "char" NOT NULL,
    match_type "char" NOT NULL,
    constrained_columns TEXT,
    referenced_columns TEXT,
    expression_tree TEXT
) ON COMMIT DROP;

CREATE TEMP TABLE _dmx_003_index_snapshot (
    index_oid OID PRIMARY KEY,
    table_oid OID NOT NULL,
    is_unique BOOLEAN NOT NULL,
    is_primary BOOLEAN NOT NULL,
    is_exclusion BOOLEAN NOT NULL,
    is_immediate BOOLEAN NOT NULL,
    is_clustered BOOLEAN NOT NULL,
    is_valid BOOLEAN NOT NULL,
    is_ready BOOLEAN NOT NULL,
    is_live BOOLEAN NOT NULL,
    key_columns TEXT NOT NULL,
    collations TEXT NOT NULL,
    operator_classes TEXT NOT NULL,
    options TEXT NOT NULL,
    expression_tree TEXT,
    predicate_tree TEXT
) ON COMMIT DROP;

CREATE TEMP TABLE _dmx_003_sequence_snapshot (
    sequence_oid OID PRIMARY KEY,
    sequence_name TEXT NOT NULL,
    table_oid OID NOT NULL,
    column_number INTEGER NOT NULL
) ON COMMIT DROP;

DO $migration$
DECLARE
    catalog_table_names CONSTANT TEXT[] := ARRAY[
        'categories',
        'locations',
        'products',
        'product_content_versions',
        'spec_definitions',
        'product_spec_values',
        'media_assets',
        'product_version_media',
        'product_location_versions'
    ];
    crawler_table_names CONSTANT TEXT[] := ARRAY[
        'product_urls',
        'crawl_runs',
        'crawl_tasks',
        'crawl_attempts',
        'crawl_observations',
        'crawl_errors',
        'product_crawl_state',
        'product_location_crawl_state',
        'discovery_sources'
    ];
    all_table_names CONSTANT TEXT[] := ARRAY[
        'categories',
        'locations',
        'products',
        'product_content_versions',
        'spec_definitions',
        'product_spec_values',
        'media_assets',
        'product_version_media',
        'product_location_versions',
        'product_urls',
        'crawl_runs',
        'crawl_tasks',
        'crawl_attempts',
        'crawl_observations',
        'crawl_errors',
        'product_crawl_state',
        'product_location_crawl_state',
        'discovery_sources'
    ];
    public_tables TEXT[];
    catalog_tables TEXT[];
    crawler_tables TEXT[];
    public_relations TEXT[];
    catalog_relations TEXT[];
    crawler_relations TEXT[];
    missing_public TEXT[];
    missing_catalog TEXT[];
    missing_crawler TEXT[];
    misplaced_catalog TEXT[];
    misplaced_crawler TEXT[];
    table_to_move TEXT;
    is_legacy BOOLEAN;
BEGIN
    SELECT COALESCE(array_agg(names.name ORDER BY names.name), ARRAY[]::TEXT[])
      INTO public_tables
      FROM unnest(all_table_names) AS names(name)
     WHERE EXISTS (
         SELECT 1
           FROM pg_catalog.pg_class AS relation
           JOIN pg_catalog.pg_namespace AS namespace
             ON namespace.oid = relation.relnamespace
          WHERE namespace.nspname = 'public'
            AND relation.relname = names.name
            AND relation.relkind IN ('r', 'p')
     );

    SELECT COALESCE(array_agg(names.name ORDER BY names.name), ARRAY[]::TEXT[])
      INTO catalog_tables
      FROM unnest(all_table_names) AS names(name)
     WHERE EXISTS (
         SELECT 1
           FROM pg_catalog.pg_class AS relation
           JOIN pg_catalog.pg_namespace AS namespace
             ON namespace.oid = relation.relnamespace
          WHERE namespace.nspname = 'catalog'
            AND relation.relname = names.name
            AND relation.relkind IN ('r', 'p')
     );

    SELECT COALESCE(array_agg(names.name ORDER BY names.name), ARRAY[]::TEXT[])
      INTO crawler_tables
      FROM unnest(all_table_names) AS names(name)
     WHERE EXISTS (
         SELECT 1
           FROM pg_catalog.pg_class AS relation
           JOIN pg_catalog.pg_namespace AS namespace
             ON namespace.oid = relation.relnamespace
          WHERE namespace.nspname = 'crawler'
            AND relation.relname = names.name
            AND relation.relkind IN ('r', 'p')
     );

    -- These arrays include views, materialized views, foreign tables, indexes,
    -- and sequences so a conflicting allow-listed name cannot be mistaken for
    -- an absent application table.
    SELECT COALESCE(array_agg(names.name ORDER BY names.name), ARRAY[]::TEXT[])
      INTO public_relations
      FROM unnest(all_table_names) AS names(name)
     WHERE EXISTS (
         SELECT 1
           FROM pg_catalog.pg_class AS relation
           JOIN pg_catalog.pg_namespace AS namespace
             ON namespace.oid = relation.relnamespace
          WHERE namespace.nspname = 'public'
            AND relation.relname = names.name
     );

    SELECT COALESCE(array_agg(names.name ORDER BY names.name), ARRAY[]::TEXT[])
      INTO catalog_relations
      FROM unnest(all_table_names) AS names(name)
     WHERE EXISTS (
         SELECT 1
           FROM pg_catalog.pg_class AS relation
           JOIN pg_catalog.pg_namespace AS namespace
             ON namespace.oid = relation.relnamespace
          WHERE namespace.nspname = 'catalog'
            AND relation.relname = names.name
     );

    SELECT COALESCE(array_agg(names.name ORDER BY names.name), ARRAY[]::TEXT[])
      INTO crawler_relations
      FROM unnest(all_table_names) AS names(name)
     WHERE EXISTS (
         SELECT 1
           FROM pg_catalog.pg_class AS relation
           JOIN pg_catalog.pg_namespace AS namespace
             ON namespace.oid = relation.relnamespace
          WHERE namespace.nspname = 'crawler'
            AND relation.relname = names.name
     );

    is_legacy :=
        cardinality(public_tables) = cardinality(all_table_names)
        AND cardinality(public_relations) = cardinality(all_table_names)
        AND cardinality(catalog_relations) = 0
        AND cardinality(crawler_relations) = 0;

    IF is_legacy THEN
        NULL;
    ELSIF
        cardinality(public_relations) = 0
        AND cardinality(catalog_tables) = cardinality(catalog_table_names)
        AND cardinality(catalog_relations) = cardinality(catalog_table_names)
        AND catalog_tables @> catalog_table_names
        AND cardinality(crawler_tables) = cardinality(crawler_table_names)
        AND cardinality(crawler_relations) = cardinality(crawler_table_names)
        AND crawler_tables @> crawler_table_names
    THEN
        is_legacy := FALSE;
    ELSE
        SELECT COALESCE(array_agg(name ORDER BY name), ARRAY[]::TEXT[])
          INTO missing_public
          FROM unnest(all_table_names) AS expected(name)
         WHERE NOT (name = ANY(public_tables));

        SELECT COALESCE(array_agg(name ORDER BY name), ARRAY[]::TEXT[])
          INTO missing_catalog
          FROM unnest(catalog_table_names) AS expected(name)
         WHERE NOT (name = ANY(catalog_tables));

        SELECT COALESCE(array_agg(name ORDER BY name), ARRAY[]::TEXT[])
          INTO missing_crawler
          FROM unnest(crawler_table_names) AS expected(name)
         WHERE NOT (name = ANY(crawler_tables));

        SELECT COALESCE(array_agg(name ORDER BY name), ARRAY[]::TEXT[])
          INTO misplaced_catalog
          FROM unnest(catalog_tables) AS present(name)
         WHERE NOT (name = ANY(catalog_table_names));

        SELECT COALESCE(array_agg(name ORDER BY name), ARRAY[]::TEXT[])
          INTO misplaced_crawler
          FROM unnest(crawler_tables) AS present(name)
         WHERE NOT (name = ANY(crawler_table_names));

        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'migration 003 found a partial, missing, duplicated, or misplaced application schema',
            DETAIL = format(
                'public tables=%s, public missing=%s, public relations=%s; '
                'catalog tables=%s, catalog missing=%s, catalog misplaced=%s, catalog relations=%s; '
                'crawler tables=%s, crawler missing=%s, crawler misplaced=%s, crawler relations=%s',
                public_tables,
                missing_public,
                public_relations,
                catalog_tables,
                missing_catalog,
                misplaced_catalog,
                catalog_relations,
                crawler_tables,
                missing_crawler,
                misplaced_crawler,
                crawler_relations
            ),
            HINT = 'Restore all 18 allow-listed tables to public, or complete the exact 9-table catalog and 9-table crawler split, before rerunning this migration.';
    END IF;

    INSERT INTO _dmx_003_table_snapshot (table_name, target_schema, table_oid)
    SELECT expected.name,
           expected.target_schema,
           relation.oid
      FROM (
          SELECT name, 'catalog'::TEXT AS target_schema
            FROM unnest(catalog_table_names) AS catalog_expected(name)
          UNION ALL
          SELECT name, 'crawler'::TEXT AS target_schema
            FROM unnest(crawler_table_names) AS crawler_expected(name)
      ) AS expected
      JOIN pg_catalog.pg_namespace AS namespace
        ON namespace.nspname = CASE
            WHEN is_legacy THEN 'public'
            ELSE expected.target_schema
        END
      JOIN pg_catalog.pg_class AS relation
        ON relation.relnamespace = namespace.oid
       AND relation.relname = expected.name
       AND relation.relkind IN ('r', 'p');

    IF (SELECT count(*) FROM _dmx_003_table_snapshot) <> cardinality(all_table_names) THEN
        RAISE EXCEPTION 'migration 003 could not snapshot all 18 allow-listed application tables';
    END IF;

    INSERT INTO _dmx_003_constraint_snapshot (
        constraint_oid,
        constraint_name,
        table_oid,
        referenced_table_oid,
        constraint_type,
        is_validated,
        is_deferrable,
        is_deferred,
        update_action,
        delete_action,
        match_type,
        constrained_columns,
        referenced_columns,
        expression_tree
    )
    SELECT constraint_object.oid,
           constraint_object.conname,
           constraint_object.conrelid,
           constraint_object.confrelid,
           constraint_object.contype,
           constraint_object.convalidated,
           constraint_object.condeferrable,
           constraint_object.condeferred,
           constraint_object.confupdtype,
           constraint_object.confdeltype,
           constraint_object.confmatchtype,
           constraint_object.conkey::TEXT,
           constraint_object.confkey::TEXT,
           constraint_object.conbin::TEXT
      FROM pg_catalog.pg_constraint AS constraint_object
     WHERE constraint_object.conrelid IN (
         SELECT table_oid FROM _dmx_003_table_snapshot
     );

    INSERT INTO _dmx_003_index_snapshot (
        index_oid,
        table_oid,
        is_unique,
        is_primary,
        is_exclusion,
        is_immediate,
        is_clustered,
        is_valid,
        is_ready,
        is_live,
        key_columns,
        collations,
        operator_classes,
        options,
        expression_tree,
        predicate_tree
    )
    SELECT index_object.indexrelid,
           index_object.indrelid,
           index_object.indisunique,
           index_object.indisprimary,
           index_object.indisexclusion,
           index_object.indimmediate,
           index_object.indisclustered,
           index_object.indisvalid,
           index_object.indisready,
           index_object.indislive,
           index_object.indkey::TEXT,
           index_object.indcollation::TEXT,
           index_object.indclass::TEXT,
           index_object.indoption::TEXT,
           index_object.indexprs::TEXT,
           index_object.indpred::TEXT
      FROM pg_catalog.pg_index AS index_object
     WHERE index_object.indrelid IN (
         SELECT table_oid FROM _dmx_003_table_snapshot
     );

    INSERT INTO _dmx_003_sequence_snapshot (
        sequence_oid,
        sequence_name,
        table_oid,
        column_number
    )
    SELECT sequence_object.oid,
           sequence_object.relname,
           ownership.refobjid,
           ownership.refobjsubid
      FROM pg_catalog.pg_depend AS ownership
      JOIN pg_catalog.pg_class AS sequence_object
        ON sequence_object.oid = ownership.objid
       AND sequence_object.relkind = 'S'
     WHERE ownership.classid = 'pg_catalog.pg_class'::regclass
       AND ownership.refclassid = 'pg_catalog.pg_class'::regclass
       AND ownership.deptype IN ('a', 'i')
       AND ownership.refobjid IN (
           SELECT table_oid FROM _dmx_003_table_snapshot
       );

    IF is_legacy THEN
        EXECUTE 'CREATE SCHEMA IF NOT EXISTS catalog';
        EXECUTE 'CREATE SCHEMA IF NOT EXISTS crawler';

        FOREACH table_to_move IN ARRAY catalog_table_names
        LOOP
            EXECUTE format(
                'ALTER TABLE %I.%I SET SCHEMA %I',
                'public',
                table_to_move,
                'catalog'
            );
        END LOOP;

        FOREACH table_to_move IN ARRAY crawler_table_names
        LOOP
            EXECUTE format(
                'ALTER TABLE %I.%I SET SCHEMA %I',
                'public',
                table_to_move,
                'crawler'
            );
        END LOOP;
    END IF;
END
$migration$;

DO $postconditions$
DECLARE
    required_index RECORD;
    required_serial RECORD;
    primary_key_count INTEGER;
    foreign_key_count INTEGER;
    unique_constraint_count INTEGER;
    check_constraint_count INTEGER;
BEGIN
    IF EXISTS (
        SELECT 1
          FROM _dmx_003_table_snapshot AS snapshot
          LEFT JOIN pg_catalog.pg_class AS relation
            ON relation.oid = snapshot.table_oid
          LEFT JOIN pg_catalog.pg_namespace AS namespace
            ON namespace.oid = relation.relnamespace
         WHERE relation.oid IS NULL
            OR relation.relname <> snapshot.table_name
            OR relation.relkind NOT IN ('r', 'p')
            OR namespace.nspname <> snapshot.target_schema
    ) THEN
        RAISE EXCEPTION 'migration 003 did not preserve table identity or intended schema placement';
    END IF;

    IF EXISTS (
        SELECT 1
          FROM _dmx_003_table_snapshot AS snapshot
          JOIN pg_catalog.pg_class AS relation
            ON relation.relname = snapshot.table_name
          JOIN pg_catalog.pg_namespace AS namespace
            ON namespace.oid = relation.relnamespace
         WHERE namespace.nspname = 'public'
    ) THEN
        RAISE EXCEPTION 'migration 003 left one or more allow-listed application relations in public';
    END IF;

    IF EXISTS (
        SELECT 1
          FROM _dmx_003_constraint_snapshot AS snapshot
          LEFT JOIN pg_catalog.pg_constraint AS current_constraint
            ON current_constraint.oid = snapshot.constraint_oid
         WHERE current_constraint.oid IS NULL
            OR current_constraint.conname <> snapshot.constraint_name
            OR current_constraint.conrelid <> snapshot.table_oid
            OR current_constraint.confrelid <> snapshot.referenced_table_oid
            OR current_constraint.contype <> snapshot.constraint_type
            OR current_constraint.convalidated <> snapshot.is_validated
            OR current_constraint.condeferrable <> snapshot.is_deferrable
            OR current_constraint.condeferred <> snapshot.is_deferred
            OR current_constraint.confupdtype <> snapshot.update_action
            OR current_constraint.confdeltype <> snapshot.delete_action
            OR current_constraint.confmatchtype <> snapshot.match_type
            OR current_constraint.conkey::TEXT IS DISTINCT FROM snapshot.constrained_columns
            OR current_constraint.confkey::TEXT IS DISTINCT FROM snapshot.referenced_columns
            OR current_constraint.conbin::TEXT IS DISTINCT FROM snapshot.expression_tree
    ) THEN
        RAISE EXCEPTION 'migration 003 changed or lost an application table constraint';
    END IF;

    IF EXISTS (
        SELECT 1
          FROM pg_catalog.pg_constraint AS foreign_key
         WHERE foreign_key.conrelid IN (
             SELECT table_oid FROM _dmx_003_table_snapshot
         )
           AND foreign_key.contype = 'f'
           AND NOT foreign_key.convalidated
    ) THEN
        RAISE EXCEPTION 'migration 003 found an unvalidated application foreign key';
    END IF;

    IF EXISTS (
        SELECT 1
          FROM _dmx_003_constraint_snapshot AS snapshot
          JOIN _dmx_003_table_snapshot AS owner_table
            ON owner_table.table_oid = snapshot.table_oid
          JOIN pg_catalog.pg_constraint AS current_constraint
            ON current_constraint.oid = snapshot.constraint_oid
          JOIN pg_catalog.pg_namespace AS namespace
            ON namespace.oid = current_constraint.connamespace
         WHERE namespace.nspname <> owner_table.target_schema
    ) THEN
        RAISE EXCEPTION 'migration 003 left an application constraint in the wrong schema';
    END IF;

    SELECT count(*) FILTER (WHERE constraint_object.contype = 'p'),
           count(*) FILTER (WHERE constraint_object.contype = 'f'),
           count(*) FILTER (WHERE constraint_object.contype = 'u'),
           count(*) FILTER (WHERE constraint_object.contype = 'c')
      INTO primary_key_count,
           foreign_key_count,
           unique_constraint_count,
           check_constraint_count
      FROM pg_catalog.pg_constraint AS constraint_object
     WHERE constraint_object.conrelid IN (
         SELECT table_oid FROM _dmx_003_table_snapshot
     );

    IF primary_key_count < 18
       OR foreign_key_count < 32
       OR unique_constraint_count < 7
       OR check_constraint_count < 3
    THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'migration 003 found fewer constraints than the baseline application schema',
            DETAIL = format(
                'primary keys=%s (minimum 18), foreign keys=%s (minimum 32), unique constraints=%s (minimum 7), check constraints=%s (minimum 3)',
                primary_key_count,
                foreign_key_count,
                unique_constraint_count,
                check_constraint_count
            );
    END IF;

    IF EXISTS (
        SELECT 1
          FROM _dmx_003_index_snapshot AS snapshot
          LEFT JOIN pg_catalog.pg_index AS current_index
            ON current_index.indexrelid = snapshot.index_oid
         WHERE current_index.indexrelid IS NULL
            OR current_index.indrelid <> snapshot.table_oid
            OR current_index.indisunique <> snapshot.is_unique
            OR current_index.indisprimary <> snapshot.is_primary
            OR current_index.indisexclusion <> snapshot.is_exclusion
            OR current_index.indimmediate <> snapshot.is_immediate
            OR current_index.indisclustered <> snapshot.is_clustered
            OR current_index.indisvalid <> snapshot.is_valid
            OR current_index.indisready <> snapshot.is_ready
            OR current_index.indislive <> snapshot.is_live
            OR current_index.indkey::TEXT <> snapshot.key_columns
            OR current_index.indcollation::TEXT <> snapshot.collations
            OR current_index.indclass::TEXT <> snapshot.operator_classes
            OR current_index.indoption::TEXT <> snapshot.options
            OR current_index.indexprs::TEXT IS DISTINCT FROM snapshot.expression_tree
            OR current_index.indpred::TEXT IS DISTINCT FROM snapshot.predicate_tree
    ) THEN
        RAISE EXCEPTION 'migration 003 changed or lost an application table index';
    END IF;

    IF EXISTS (
        SELECT 1
          FROM _dmx_003_index_snapshot AS snapshot
          JOIN _dmx_003_table_snapshot AS owner_table
            ON owner_table.table_oid = snapshot.table_oid
          JOIN pg_catalog.pg_class AS index_relation
            ON index_relation.oid = snapshot.index_oid
          JOIN pg_catalog.pg_namespace AS namespace
            ON namespace.oid = index_relation.relnamespace
         WHERE namespace.nspname <> owner_table.target_schema
    ) THEN
        RAISE EXCEPTION 'migration 003 left an application index in the wrong schema';
    END IF;

    FOR required_index IN
        SELECT *
          FROM (
              VALUES
                  ('catalog', 'products', 'uq_products_source_key', TRUE, TRUE),
                  ('catalog', 'product_content_versions', 'uq_product_content_current', TRUE, TRUE),
                  ('catalog', 'product_content_versions', 'ix_product_content_history', FALSE, FALSE),
                  ('catalog', 'product_spec_values', 'ix_product_spec_values_order', FALSE, FALSE),
                  ('catalog', 'product_location_versions', 'uq_product_location_current', TRUE, TRUE),
                  ('catalog', 'product_location_versions', 'ix_product_location_history', FALSE, FALSE),
                  ('crawler', 'crawl_tasks', 'ix_tasks_ready', FALSE, FALSE),
                  ('crawler', 'crawl_errors', 'ix_errors_retry', FALSE, FALSE)
          ) AS expected(
              schema_name,
              table_name,
              index_name,
              must_be_unique,
              must_be_partial
          )
    LOOP
        IF NOT EXISTS (
            SELECT 1
              FROM pg_catalog.pg_index AS index_object
              JOIN pg_catalog.pg_class AS index_relation
                ON index_relation.oid = index_object.indexrelid
              JOIN pg_catalog.pg_class AS table_relation
                ON table_relation.oid = index_object.indrelid
              JOIN pg_catalog.pg_namespace AS namespace
                ON namespace.oid = table_relation.relnamespace
             WHERE namespace.nspname = required_index.schema_name
               AND table_relation.relname = required_index.table_name
               AND index_relation.relname = required_index.index_name
               AND index_object.indisvalid
               AND index_object.indisready
               AND (
                   NOT required_index.must_be_unique
                   OR index_object.indisunique
               )
               AND (
                   NOT required_index.must_be_partial
                   OR index_object.indpred IS NOT NULL
               )
        ) THEN
            RAISE EXCEPTION 'migration 003 is missing required index %.%',
                required_index.schema_name,
                required_index.index_name;
        END IF;
    END LOOP;

    IF EXISTS (
        SELECT 1
          FROM _dmx_003_sequence_snapshot AS snapshot
          JOIN _dmx_003_table_snapshot AS owner_table
            ON owner_table.table_oid = snapshot.table_oid
          LEFT JOIN pg_catalog.pg_class AS sequence_relation
            ON sequence_relation.oid = snapshot.sequence_oid
           AND sequence_relation.relkind = 'S'
          LEFT JOIN pg_catalog.pg_namespace AS namespace
            ON namespace.oid = sequence_relation.relnamespace
         WHERE sequence_relation.oid IS NULL
            OR sequence_relation.relname <> snapshot.sequence_name
            OR namespace.nspname <> owner_table.target_schema
            OR NOT EXISTS (
                SELECT 1
                  FROM pg_catalog.pg_depend AS ownership
                 WHERE ownership.classid = 'pg_catalog.pg_class'::regclass
                   AND ownership.objid = snapshot.sequence_oid
                   AND ownership.refclassid = 'pg_catalog.pg_class'::regclass
                   AND ownership.refobjid = snapshot.table_oid
                   AND ownership.refobjsubid = snapshot.column_number
                   AND ownership.deptype IN ('a', 'i')
            )
            OR NOT EXISTS (
                SELECT 1
                  FROM pg_catalog.pg_attribute AS column_object
                  JOIN pg_catalog.pg_attrdef AS column_default
                    ON column_default.adrelid = column_object.attrelid
                   AND column_default.adnum = column_object.attnum
                 WHERE column_object.attrelid = snapshot.table_oid
                   AND column_object.attnum = snapshot.column_number
                   AND column_object.atthasdef
                   AND position(
                       'nextval(' IN pg_catalog.pg_get_expr(
                           column_default.adbin,
                           column_default.adrelid
                       )
                   ) > 0
                   AND EXISTS (
                       SELECT 1
                         FROM pg_catalog.pg_depend AS default_dependency
                        WHERE default_dependency.classid = 'pg_catalog.pg_attrdef'::regclass
                          AND default_dependency.objid = column_default.oid
                          AND default_dependency.refclassid = 'pg_catalog.pg_class'::regclass
                          AND default_dependency.refobjid = snapshot.sequence_oid
                   )
            )
    ) THEN
        RAISE EXCEPTION 'migration 003 changed or lost an owned sequence or its column default';
    END IF;

    FOR required_serial IN
        SELECT *
          FROM (
              VALUES
                  ('catalog', 'categories', 'id'),
                  ('catalog', 'locations', 'id'),
                  ('catalog', 'spec_definitions', 'id'),
                  ('catalog', 'product_spec_values', 'id'),
                  ('crawler', 'product_urls', 'id'),
                  ('crawler', 'crawl_attempts', 'id'),
                  ('crawler', 'crawl_errors', 'id'),
                  ('crawler', 'crawl_observations', 'id')
          ) AS expected(schema_name, table_name, column_name)
    LOOP
        IF (
            SELECT count(*)
              FROM pg_catalog.pg_class AS table_relation
              JOIN pg_catalog.pg_namespace AS table_namespace
                ON table_namespace.oid = table_relation.relnamespace
              JOIN pg_catalog.pg_attribute AS column_object
                ON column_object.attrelid = table_relation.oid
               AND column_object.attname = required_serial.column_name
               AND NOT column_object.attisdropped
              JOIN pg_catalog.pg_depend AS ownership
                ON ownership.refclassid = 'pg_catalog.pg_class'::regclass
               AND ownership.refobjid = table_relation.oid
               AND ownership.refobjsubid = column_object.attnum
               AND ownership.classid = 'pg_catalog.pg_class'::regclass
               AND ownership.deptype IN ('a', 'i')
              JOIN pg_catalog.pg_class AS sequence_relation
                ON sequence_relation.oid = ownership.objid
               AND sequence_relation.relkind = 'S'
              JOIN pg_catalog.pg_namespace AS sequence_namespace
                ON sequence_namespace.oid = sequence_relation.relnamespace
             WHERE table_namespace.nspname = required_serial.schema_name
               AND table_relation.relname = required_serial.table_name
               AND sequence_namespace.nspname = required_serial.schema_name
        ) <> 1 THEN
            RAISE EXCEPTION 'migration 003 expected one owned sequence for %.%.%',
                required_serial.schema_name,
                required_serial.table_name,
                required_serial.column_name;
        END IF;
    END LOOP;
END
$postconditions$;

COMMIT;
