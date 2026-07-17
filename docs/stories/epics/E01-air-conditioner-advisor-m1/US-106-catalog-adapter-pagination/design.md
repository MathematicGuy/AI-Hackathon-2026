# Design

- `CatalogAdapter` reads a JSON list from an injected path and does not mutate it.
- `AirConditionerFilters` is internal and accepts only category `air_conditioner` plus optional region.
- Cursor is an integer index into the stable pre-exclusion candidate stream.
- Search scans forward, skips excluded product IDs, and returns the next scan index.
- `total_candidates` is counted before exclusions; `source_snapshot` must be identical across candidates.
- Invalid limit/cursor/catalog/snapshot input fails explicitly.
