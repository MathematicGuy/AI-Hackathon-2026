-- Product catalog schema.
-- Original product columns are preserved verbatim inside products.attributes
-- (JSONB, keys = exact original headers). The typed columns are copies of
-- existing columns used only for indexing/joins, plus provenance metadata.

-- Shared import lineage for every ingestion type.
CREATE TABLE IF NOT EXISTS import_runs (
    id           bigserial PRIMARY KEY,
    source_label text NOT NULL,
    started_at   timestamptz NOT NULL DEFAULT now(),
    finished_at  timestamptz,
    status       text NOT NULL DEFAULT 'running',
    rows_ok      integer NOT NULL DEFAULT 0,
    rows_skipped integer NOT NULL DEFAULT 0,
    rows_error   integer NOT NULL DEFAULT 0,
    details      jsonb NOT NULL DEFAULT '{}'::jsonb
);

-- Brand reference. Brand name exists in all 14 categories; brand_id only in 9.
CREATE TABLE IF NOT EXISTS brands (
    brand    text PRIMARY KEY,
    brand_id text
);

-- Category reference. One category_code per sheet/ngành.
CREATE TABLE IF NOT EXISTS categories (
    category_code text PRIMARY KEY,
    sheet_name    text NOT NULL
);

-- Products. attributes holds the entire original row unchanged.
-- sku is the unique business key (unique across all 14 sheets, never null).
-- productidweb is NOT unique: variants can share one web listing id.
CREATE TABLE IF NOT EXISTS products (
    id            bigserial PRIMARY KEY,
    sku           text NOT NULL UNIQUE,
    productidweb  text,
    model_code    text,
    category_code text REFERENCES categories (category_code),
    brand         text REFERENCES brands (brand),
    brand_id      text,
    sheet_name    text NOT NULL,
    attributes    jsonb NOT NULL,
    source_file   text NOT NULL,
    content_hash  text NOT NULL,
    import_run_id bigint REFERENCES import_runs (id),
    updated_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_products_productidweb ON products (productidweb);
CREATE INDEX IF NOT EXISTS idx_products_category ON products (category_code);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products (brand);
CREATE INDEX IF NOT EXISTS idx_products_attributes ON products USING gin (attributes);
