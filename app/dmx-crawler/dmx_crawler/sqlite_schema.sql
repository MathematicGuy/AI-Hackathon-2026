PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    province_id INTEGER NOT NULL,
    province_name TEXT NOT NULL DEFAULT '',
    ward_id INTEGER NOT NULL,
    ward_name TEXT NOT NULL DEFAULT '',
    address TEXT NOT NULL DEFAULT '',
    config_hash TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS crawl_runs (
    id TEXT PRIMARY KEY,
    parent_run_id TEXT REFERENCES crawl_runs(id),
    command TEXT NOT NULL,
    mode TEXT NOT NULL,
    status TEXT NOT NULL,
    arguments_json TEXT NOT NULL DEFAULT '{}',
    config_hash TEXT,
    code_version TEXT,
    counters_json TEXT NOT NULL DEFAULT '{}',
    blocked_reason TEXT,
    started_at TEXT NOT NULL,
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL DEFAULT 'dienmayxanh',
    source_product_key TEXT,
    canonical_url TEXT NOT NULL,
    canonical_url_hash TEXT NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    status TEXT NOT NULL DEFAULT 'active',
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    sitemap_lastmod TEXT,
    UNIQUE(source, canonical_url_hash)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_products_source_key
    ON products(source, source_product_key) WHERE source_product_key IS NOT NULL;

CREATE TABLE IF NOT EXISTS product_urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    source TEXT NOT NULL DEFAULT 'dienmayxanh',
    url TEXT NOT NULL,
    url_hash TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'canonical',
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    UNIQUE(source, url_hash)
);

CREATE TABLE IF NOT EXISTS crawl_tasks (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES crawl_runs(id) ON DELETE CASCADE,
    task_type TEXT NOT NULL,
    target_key TEXT NOT NULL,
    product_id TEXT REFERENCES products(id),
    location_id INTEGER REFERENCES locations(id),
    url TEXT,
    status TEXT NOT NULL DEFAULT 'queued',
    priority INTEGER NOT NULL DEFAULT 100,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    available_at TEXT NOT NULL,
    leased_until TEXT,
    leased_by TEXT,
    created_at TEXT NOT NULL,
    finished_at TEXT,
    UNIQUE(run_id, task_type, target_key)
);
CREATE INDEX IF NOT EXISTS ix_tasks_ready ON crawl_tasks(status, available_at, priority);

CREATE TABLE IF NOT EXISTS crawl_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT REFERENCES crawl_tasks(id) ON DELETE CASCADE,
    attempt_no INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    http_status INTEGER,
    latency_ms INTEGER,
    request_url TEXT,
    response_url TEXT,
    requested_location TEXT,
    returned_location_json TEXT,
    location_matched INTEGER,
    outcome TEXT,
    error_kind TEXT,
    retry_after TEXT,
    response_metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS crawl_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT REFERENCES crawl_runs(id),
    task_id TEXT REFERENCES crawl_tasks(id),
    attempt_id INTEGER REFERENCES crawl_attempts(id),
    product_id TEXT REFERENCES products(id),
    location_id INTEGER REFERENCES locations(id),
    error_kind TEXT NOT NULL,
    message TEXT NOT NULL,
    traceback TEXT,
    http_status INTEGER,
    retryable INTEGER NOT NULL DEFAULT 0,
    context_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    resolved_by_task_id TEXT REFERENCES crawl_tasks(id)
);
CREATE INDEX IF NOT EXISTS ix_errors_retry ON crawl_errors(retryable, resolved_at, created_at);

CREATE TABLE IF NOT EXISTS product_content_versions (
    id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories(id),
    name TEXT NOT NULL,
    brand TEXT,
    model TEXT,
    product_code TEXT,
    description TEXT,
    rating REAL,
    rating_count INTEGER,
    sold_count INTEGER,
    stock_status TEXT NOT NULL DEFAULT 'unknown',
    stock_raw TEXT,
    specs_raw_json TEXT NOT NULL DEFAULT '[]',
    content_hash TEXT NOT NULL,
    valid_from TEXT NOT NULL,
    valid_to TEXT,
    created_by_task_id TEXT REFERENCES crawl_tasks(id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_product_content_current
    ON product_content_versions(product_id) WHERE valid_to IS NULL;
CREATE INDEX IF NOT EXISTS ix_product_content_history
    ON product_content_versions(product_id, valid_from DESC);

CREATE TABLE IF NOT EXISTS spec_definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES categories(id),
    normalized_key TEXT NOT NULL,
    canonical_label TEXT NOT NULL,
    data_type TEXT NOT NULL DEFAULT 'text',
    unit TEXT,
    aliases_json TEXT NOT NULL DEFAULT '[]',
    UNIQUE(category_id, normalized_key)
);

CREATE TABLE IF NOT EXISTS product_spec_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_version_id TEXT NOT NULL REFERENCES product_content_versions(id) ON DELETE CASCADE,
    definition_id INTEGER REFERENCES spec_definitions(id),
    group_name TEXT,
    group_ordinal INTEGER NOT NULL DEFAULT 0,
    raw_label TEXT NOT NULL,
    raw_value TEXT NOT NULL,
    value_text TEXT,
    value_number REAL,
    value_boolean INTEGER,
    value_json TEXT,
    unit TEXT,
    item_ordinal INTEGER NOT NULL DEFAULT 0,
    source TEXT NOT NULL DEFAULT 'dom',
    provenance_json TEXT NOT NULL DEFAULT '[]',
    normalized_value_json TEXT,
    ordinal INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_product_spec_values_order
    ON product_spec_values(content_version_id, group_ordinal, item_ordinal, id);

CREATE TABLE IF NOT EXISTS media_assets (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    url_hash TEXT NOT NULL UNIQUE,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS product_version_media (
    content_version_id TEXT NOT NULL REFERENCES product_content_versions(id) ON DELETE CASCADE,
    media_id TEXT NOT NULL REFERENCES media_assets(id),
    role TEXT NOT NULL DEFAULT 'gallery',
    ordinal INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(content_version_id, media_id)
);

CREATE TABLE IF NOT EXISTS product_location_versions (
    id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    location_id INTEGER NOT NULL REFERENCES locations(id),
    sale_price INTEGER,
    list_price INTEGER,
    currency TEXT NOT NULL DEFAULT 'VND',
    promotion_json TEXT NOT NULL DEFAULT '{}',
    stock_status TEXT NOT NULL DEFAULT 'unknown',
    stock_raw TEXT,
    delivery_json TEXT NOT NULL DEFAULT '{}',
    returned_location_json TEXT NOT NULL DEFAULT '{}',
    state_hash TEXT NOT NULL,
    valid_from TEXT NOT NULL,
    valid_to TEXT,
    created_by_task_id TEXT REFERENCES crawl_tasks(id)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_product_location_current
    ON product_location_versions(product_id, location_id) WHERE valid_to IS NULL;
CREATE INDEX IF NOT EXISTS ix_product_location_history
    ON product_location_versions(product_id, location_id, valid_from DESC);

CREATE TABLE IF NOT EXISTS crawl_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT REFERENCES crawl_tasks(id),
    product_id TEXT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    location_id INTEGER REFERENCES locations(id),
    content_version_id TEXT REFERENCES product_content_versions(id),
    location_version_id TEXT REFERENCES product_location_versions(id),
    changed INTEGER NOT NULL,
    observed_at TEXT NOT NULL,
    response_hash TEXT
);

CREATE TABLE IF NOT EXISTS product_crawl_state (
    product_id TEXT PRIMARY KEY REFERENCES products(id) ON DELETE CASCADE,
    last_attempt_at TEXT,
    last_success_at TEXT,
    last_changed_at TEXT,
    next_due_at TEXT,
    etag TEXT,
    last_modified TEXT,
    last_response_hash TEXT,
    consecutive_unchanged INTEGER NOT NULL DEFAULT 0,
    failure_streak INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS product_location_crawl_state (
    product_id TEXT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    location_id INTEGER NOT NULL REFERENCES locations(id),
    last_attempt_at TEXT,
    last_success_at TEXT,
    last_changed_at TEXT,
    next_due_at TEXT,
    last_response_hash TEXT,
    consecutive_unchanged INTEGER NOT NULL DEFAULT 0,
    failure_streak INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(product_id, location_id)
);

CREATE TABLE IF NOT EXISTS discovery_sources (
    url TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    etag TEXT,
    last_modified TEXT,
    content_hash TEXT,
    last_checked_at TEXT,
    last_success_at TEXT
);
