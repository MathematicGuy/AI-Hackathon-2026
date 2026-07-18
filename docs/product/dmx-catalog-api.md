# DMX Catalog API and SQLite Integration

## Goal

Serve the Next.js frontend from the DMX crawler SQLite database while keeping
crawler observations separate from editorial homepage content. SQLite is the
temporary runtime database. The HTTP contract is database-agnostic so a later
move to PostgreSQL does not require a frontend rewrite.

The machine-readable contract is
`docs/contracts/dmx-catalog-api-v1.yaml`.

## Runtime Boundary

```text
DMX crawler -> data/dmx.db -> catalog API -> Next.js server components
                                   |
                                   +-> browser clients
```

The browser must never open or download the SQLite file. Only the API process
opens `dmx.db`. The initial API may be implemented in Python beside the
crawler and reuse `Database.export_current()`, but responses must follow the
v1 contract rather than exposing database rows directly.

Recommended local environment variables:

```text
DMX_DATABASE_URL=sqlite:///app/dmx-crawler/data/dmx.db
NEXT_PUBLIC_CATALOG_API_URL=http://localhost:8000
```

`NEXT_PUBLIC_CATALOG_API_URL` is safe only for the public API origin. The
database path must remain server-only.

## Read Model

Every product response represents one product, not one SQL join row. A product
may contain several location snapshots.

Current product content:

- `products` supplies identity and canonical URL.
- `categories` supplies the crawler category code.
- `product_content_versions WHERE valid_to IS NULL` supplies current content.
- `product_version_media` and `media_assets` supply ordered images.
- `product_spec_values` supplies ordered specification groups.
- `product_location_versions WHERE valid_to IS NULL` and `locations` supply
  current price, promotion, stock, and delivery per location.

The API groups all location rows into `locations[]`. When the request includes
`location=hcm`, `selected_location` is the HCM snapshot. If it is missing,
the API returns `selected_location: null`; it must not silently substitute a
different city's price.

## Endpoints

| Endpoint | Frontend use |
| --- | --- |
| `GET /api/v1/home?location=hcm` | One request for homepage collections and editorial content |
| `GET /api/v1/products` | Category pages, search, pagination |
| `GET /api/v1/products/{slug}` | Product detail page |
| `GET /api/v1/categories` | Category navigation |
| `GET /api/v1/locations` | Location selector |
| `GET /api/v1/health` | Local/container readiness |

List filters are `category`, `location`, `q`, `collection`, `limit`,
and opaque `cursor`. The first version uses a maximum limit of 100.

## Frontend Mapping

| API field | Existing `ProductItem` |
| --- | --- |
| `id` | `id` |
| `name` | `name` |
| `model ?? brand ?? ""` | `sub` |
| `selected_location.sale_price` | `price` after the FE view model supports a nullable/unavailable state |
| `selected_location.list_price` | `originalPrice` |
| computed percentage | `discount` |
| `rating` | `rating` |
| formatted `sold_count` | `soldLabel` |
| `images[0]?.url` | `src` |
| `canonical_url` | `href` |
| `category.code` | `category` |
| `description` | `description` |
| selected spec display values | `highlights` |

The API returns null for unknown prices. The frontend adapter may display
"Liên hệ" but must not convert null into zero. Discount exists only when both
prices are positive and `list_price > sale_price`.

The frontend should introduce DTO types matching the OpenAPI contract and keep
`ProductItem` as a view model. A single adapter converts DTOs into the
existing cards so UI components do not depend on database naming.

## SQLite Extension for Existing Frontend Mock Data

Crawler tables remain append/version oriented. Editorial mock content needs a
separate namespace:

```sql
CREATE TABLE site_content_entries (
    id TEXT PRIMARY KEY,
    content_type TEXT NOT NULL,
    code TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    sort_order INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1,
    valid_from TEXT,
    valid_to TEXT,
    updated_at TEXT NOT NULL,
    UNIQUE(content_type, code)
);

CREATE TABLE product_collections (
    id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    active INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL
);

CREATE TABLE product_collection_items (
    collection_id TEXT NOT NULL REFERENCES product_collections(id) ON DELETE CASCADE,
    product_id TEXT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    override_json TEXT NOT NULL DEFAULT '{}',
    PRIMARY KEY (collection_id, product_id),
    UNIQUE (collection_id, position)
);
```

Content mapping:

| `home-data.ts` section | SQLite target |
| --- | --- |
| `heroSlides` | `site_content_entries(content_type='hero')` |
| `utilityBanners` | `site_content_entries(content_type='utility_banner')` |
| category badge/image/description | `site_content_entries(content_type='category_presentation')` |
| `flashTabs`, `featuredTabs` | collection `payload_json` |
| `flashProducts` | `product_collections(code='flash-sale')` items |
| `featuredProducts` | `product_collections(code='featured')` items |
| `weeklyBanners` | `site_content_entries(content_type='weekly_banner')` |
| `articles` | `site_content_entries(content_type='article')` |
| `searchTags` | `site_content_entries(content_type='search_tag')` |
| `supportContacts` | `site_content_entries(content_type='support_contact')` |

`override_json` is limited to presentation data such as CTA label, slot
remaining, campaign badge, or campaign-specific copy. Price, stock, rating,
specifications, and canonical product identity must come from crawler tables.

## Importing Mock Products

Import is a one-time, idempotent seed operation:

1. Normalize each mock `href` and compute the same canonical URL hash as the
   crawler.
2. Match an existing crawler product by canonical URL hash, regardless of its
   current source. If found, reference it from the collection.
3. If not found, create a temporary `products` row with
   `source='frontend_mock'`, followed by one current
   `product_content_versions` row and one optional mock location row.
4. Store campaign-only fields in `product_collection_items.override_json`.
5. When the crawler later finds the same canonical URL, reconcile the seed to
   the crawler identity in one transaction, repoint collection items, then
   remove the temporary mock versions.

Until reconciliation is implemented, the API must deduplicate by canonical URL
hash and prefer sources in this order:

```text
dienmayxanh > fixture > frontend_mock
```

Do not import articles as products merely because the current TypeScript type
reuses `ProductItem`. They belong to `site_content_entries`.

## Core Query Shape

```sql
SELECT
  p.id,
  p.canonical_url,
  c.code AS category_code,
  c.name AS category_name,
  pcv.name,
  pcv.brand,
  pcv.model,
  pcv.description,
  pcv.rating,
  pcv.rating_count,
  pcv.sold_count,
  pcv.valid_from AS content_observed_at
FROM products p
JOIN categories c ON c.id = p.category_id
JOIN product_content_versions pcv
  ON pcv.product_id = p.id AND pcv.valid_to IS NULL
WHERE p.status = 'active';
```

Media, specs, and location snapshots should be loaded in bounded secondary
queries for the selected product IDs, then grouped in application code. Avoid
one large media x specs x locations join because it multiplies rows.

## Error and Cache Rules

- `400`: invalid query or unsupported location/category.
- `404`: product slug does not exist.
- `500`: database/query failure, without exposing SQL paths or tracebacks.
- All responses include `meta.request_id`; logs may contain it but never
  cookies or customer addresses.
- Product lists may use `Cache-Control: public, s-maxage=300`.
- Product detail may use a 60-second revalidation window.
- Local SQLite uses WAL mode, foreign keys, a busy timeout, and one writer
  transaction at a time. API requests are read-only.

## Delivery Sequence

1. Merge or copy the crawler component into the working branch.
2. Add the three editorial/collection tables as an idempotent SQLite migration.
3. Add a mock-data seed command and reconciliation tests.
4. Implement the v1 API against a read-only catalog repository.
5. Generate or hand-write FE DTOs from OpenAPI and add the DTO-to-view adapter.
6. Replace `fetchHomePageData()` and synchronous `catalog.ts` lookups.
7. Validate list, detail, category, search, location selection, and empty-price
   behavior with a temporary SQLite fixture.
