BEGIN;

CREATE TABLE IF NOT EXISTS categories (
    id BIGSERIAL PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS locations (
    id BIGSERIAL PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    province_id BIGINT NOT NULL,
    province_name TEXT NOT NULL DEFAULT '',
    ward_id BIGINT NOT NULL,
    ward_name TEXT NOT NULL DEFAULT '',
    address TEXT NOT NULL DEFAULT '',
    config_hash CHAR(64) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS crawl_runs (
    id UUID PRIMARY KEY,
    parent_run_id UUID REFERENCES crawl_runs(id),
    command TEXT NOT NULL,
    mode TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('planned','running','succeeded','partial','blocked','failed')),
    arguments_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    config_hash CHAR(64),
    code_version TEXT,
    counters_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    blocked_reason TEXT,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY,
    source TEXT NOT NULL DEFAULT 'dienmayxanh',
    source_product_key TEXT,
    canonical_url TEXT NOT NULL,
    canonical_url_hash CHAR(64) NOT NULL,
    category_id BIGINT REFERENCES categories(id),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','unavailable','retired')),
    first_seen_at TIMESTAMPTZ NOT NULL,
    last_seen_at TIMESTAMPTZ NOT NULL,
    sitemap_lastmod DATE,
    UNIQUE(source, canonical_url_hash)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_products_source_key
    ON products(source, source_product_key) WHERE source_product_key IS NOT NULL;

CREATE TABLE IF NOT EXISTS product_urls (
    id BIGSERIAL PRIMARY KEY,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    source TEXT NOT NULL DEFAULT 'dienmayxanh',
    url TEXT NOT NULL,
    url_hash CHAR(64) NOT NULL,
    kind TEXT NOT NULL DEFAULT 'canonical',
    first_seen_at TIMESTAMPTZ NOT NULL,
    last_seen_at TIMESTAMPTZ NOT NULL,
    UNIQUE(source, url_hash)
);

CREATE TABLE IF NOT EXISTS crawl_tasks (
    id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES crawl_runs(id) ON DELETE CASCADE,
    task_type TEXT NOT NULL CHECK (task_type IN ('discover','common_product','location_product')),
    target_key TEXT NOT NULL,
    product_id UUID REFERENCES products(id),
    location_id BIGINT REFERENCES locations(id),
    url TEXT,
    status TEXT NOT NULL DEFAULT 'queued',
    priority INTEGER NOT NULL DEFAULT 100,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    available_at TIMESTAMPTZ NOT NULL,
    leased_until TIMESTAMPTZ,
    leased_by TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    UNIQUE(run_id, task_type, target_key)
);
CREATE INDEX IF NOT EXISTS ix_tasks_ready ON crawl_tasks(status, available_at, priority);

CREATE TABLE IF NOT EXISTS crawl_attempts (
    id BIGSERIAL PRIMARY KEY,
    task_id UUID REFERENCES crawl_tasks(id) ON DELETE CASCADE,
    attempt_no INTEGER NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    http_status INTEGER,
    latency_ms INTEGER,
    request_url TEXT,
    response_url TEXT,
    requested_location TEXT,
    returned_location_json JSONB,
    location_matched BOOLEAN,
    outcome TEXT,
    error_kind TEXT,
    retry_after TIMESTAMPTZ,
    response_metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS crawl_errors (
    id BIGSERIAL PRIMARY KEY,
    run_id UUID REFERENCES crawl_runs(id),
    task_id UUID REFERENCES crawl_tasks(id),
    attempt_id BIGINT REFERENCES crawl_attempts(id),
    product_id UUID REFERENCES products(id),
    location_id BIGINT REFERENCES locations(id),
    error_kind TEXT NOT NULL,
    message TEXT NOT NULL,
    traceback TEXT,
    http_status INTEGER,
    retryable BOOLEAN NOT NULL DEFAULT FALSE,
    context_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL,
    resolved_at TIMESTAMPTZ,
    resolved_by_task_id UUID REFERENCES crawl_tasks(id)
);
CREATE INDEX IF NOT EXISTS ix_errors_retry ON crawl_errors(retryable, resolved_at, created_at);

CREATE TABLE IF NOT EXISTS product_content_versions (
    id UUID PRIMARY KEY,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    category_id BIGINT NOT NULL REFERENCES categories(id),
    name TEXT NOT NULL,
    brand TEXT,
    model TEXT,
    product_code TEXT,
    description TEXT,
    rating NUMERIC(3,2),
    rating_count BIGINT,
    sold_count BIGINT,
    stock_status TEXT NOT NULL DEFAULT 'unknown',
    stock_raw TEXT,
    specs_raw_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    content_hash CHAR(64) NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ,
    created_by_task_id UUID REFERENCES crawl_tasks(id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_product_content_current
    ON product_content_versions(product_id) WHERE valid_to IS NULL;
CREATE INDEX IF NOT EXISTS ix_product_content_history
    ON product_content_versions(product_id, valid_from DESC);

CREATE TABLE IF NOT EXISTS spec_definitions (
    id BIGSERIAL PRIMARY KEY,
    category_id BIGINT NOT NULL REFERENCES categories(id),
    normalized_key TEXT NOT NULL,
    canonical_label TEXT NOT NULL,
    data_type TEXT NOT NULL DEFAULT 'text',
    unit TEXT,
    aliases_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    UNIQUE(category_id, normalized_key)
);

CREATE TABLE IF NOT EXISTS product_spec_values (
    id BIGSERIAL PRIMARY KEY,
    content_version_id UUID NOT NULL REFERENCES product_content_versions(id) ON DELETE CASCADE,
    definition_id BIGINT REFERENCES spec_definitions(id),
    group_name TEXT,
    group_ordinal INTEGER NOT NULL DEFAULT 0,
    raw_label TEXT NOT NULL,
    raw_value TEXT NOT NULL,
    value_text TEXT,
    value_number NUMERIC,
    value_boolean BOOLEAN,
    value_json JSONB,
    unit TEXT,
    item_ordinal INTEGER NOT NULL DEFAULT 0,
    source TEXT NOT NULL DEFAULT 'dom',
    provenance_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    normalized_value_json JSONB,
    ordinal INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_product_spec_values_order
    ON product_spec_values(content_version_id, group_ordinal, item_ordinal, id);

CREATE TABLE IF NOT EXISTS media_assets (
    id UUID PRIMARY KEY,
    url TEXT NOT NULL,
    url_hash CHAR(64) NOT NULL UNIQUE,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS product_version_media (
    content_version_id UUID NOT NULL REFERENCES product_content_versions(id) ON DELETE CASCADE,
    media_id UUID NOT NULL REFERENCES media_assets(id),
    role TEXT NOT NULL DEFAULT 'gallery',
    ordinal INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(content_version_id, media_id)
);

CREATE TABLE IF NOT EXISTS product_location_versions (
    id UUID PRIMARY KEY,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    location_id BIGINT NOT NULL REFERENCES locations(id),
    sale_price BIGINT,
    list_price BIGINT,
    currency CHAR(3) NOT NULL DEFAULT 'VND',
    promotion_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    stock_status TEXT NOT NULL DEFAULT 'unknown',
    stock_raw TEXT,
    delivery_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    returned_location_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    state_hash CHAR(64) NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ,
    created_by_task_id UUID REFERENCES crawl_tasks(id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_product_location_current
    ON product_location_versions(product_id, location_id) WHERE valid_to IS NULL;
CREATE INDEX IF NOT EXISTS ix_product_location_history
    ON product_location_versions(product_id, location_id, valid_from DESC);

CREATE TABLE IF NOT EXISTS crawl_observations (
    id BIGSERIAL PRIMARY KEY,
    task_id UUID REFERENCES crawl_tasks(id),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    location_id BIGINT REFERENCES locations(id),
    content_version_id UUID REFERENCES product_content_versions(id),
    location_version_id UUID REFERENCES product_location_versions(id),
    changed BOOLEAN NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    response_hash CHAR(64)
);

CREATE TABLE IF NOT EXISTS product_crawl_state (
    product_id UUID PRIMARY KEY REFERENCES products(id) ON DELETE CASCADE,
    last_attempt_at TIMESTAMPTZ,
    last_success_at TIMESTAMPTZ,
    last_changed_at TIMESTAMPTZ,
    next_due_at TIMESTAMPTZ,
    etag TEXT,
    last_modified TEXT,
    last_response_hash CHAR(64),
    consecutive_unchanged INTEGER NOT NULL DEFAULT 0,
    failure_streak INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS product_location_crawl_state (
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    location_id BIGINT NOT NULL REFERENCES locations(id),
    last_attempt_at TIMESTAMPTZ,
    last_success_at TIMESTAMPTZ,
    last_changed_at TIMESTAMPTZ,
    next_due_at TIMESTAMPTZ,
    last_response_hash CHAR(64),
    consecutive_unchanged INTEGER NOT NULL DEFAULT 0,
    failure_streak INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(product_id, location_id)
);

CREATE TABLE IF NOT EXISTS discovery_sources (
    url TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    etag TEXT,
    last_modified TEXT,
    content_hash CHAR(64),
    last_checked_at TIMESTAMPTZ,
    last_success_at TIMESTAMPTZ
);

COMMIT;
