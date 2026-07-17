-- Backfill the rich, ordered specification columns for databases that were
-- initialized from 001_initial.sql before grouped specs were introduced.
-- This file is intentionally not executed by the test suite or this task.
BEGIN;

ALTER TABLE product_content_versions ALTER COLUMN specs_raw_json SET DEFAULT '[]'::jsonb;
ALTER TABLE product_spec_values ADD COLUMN IF NOT EXISTS group_ordinal INTEGER NOT NULL DEFAULT 0;
ALTER TABLE product_spec_values ADD COLUMN IF NOT EXISTS value_text TEXT;
ALTER TABLE product_spec_values ADD COLUMN IF NOT EXISTS value_number NUMERIC;
ALTER TABLE product_spec_values ADD COLUMN IF NOT EXISTS value_boolean BOOLEAN;
ALTER TABLE product_spec_values ADD COLUMN IF NOT EXISTS value_json JSONB;
ALTER TABLE product_spec_values ADD COLUMN IF NOT EXISTS unit TEXT;
ALTER TABLE product_spec_values ADD COLUMN IF NOT EXISTS item_ordinal INTEGER NOT NULL DEFAULT 0;
ALTER TABLE product_spec_values ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'dom';
ALTER TABLE product_spec_values ADD COLUMN IF NOT EXISTS provenance_json JSONB NOT NULL DEFAULT '[]'::jsonb;

CREATE INDEX IF NOT EXISTS ix_product_spec_values_order
    ON product_spec_values(content_version_id, group_ordinal, item_ordinal, id);

COMMIT;
