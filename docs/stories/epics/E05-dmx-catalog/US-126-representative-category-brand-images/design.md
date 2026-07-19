# US-126 Design

## Domain Model

- `RepresentativeGroup`: `category_code`, nullable `brand_id`, `brand`, and an
  explicit first-party `source_url`.
- `RepresentativeImageMapping`: versioned group metadata plus zero to three
  normalized image URLs and their source page.
- `AssignedImage`: SKU, selected image URL, group key, mapping version, and the
  constant `image_type="representative"`.
- `RepresentativeImageProjection`: nullable Agent API fields for the first
  product presented in a turn. A mapped group uses the selected CDN URL; an
  unmapped group uses the common placeholder.

The normal group key is `<category_code>:<brand_id>`. Because five catalog
sheets omit `brand_id`, the safe fallback is
`<category_code>:brand:<normalized-brand>`; a null brand ID must never collapse
different brands into one group.

## Application Flow

1. Require exactly one explicit mode: `--pilot` or `--all-groups`. The pilot
   uses five frozen groups; all-groups derives unique groups from the catalog
   and deterministic first-party category/brand URL slugs. No search API is
   called.
2. Fetch each `https://www.dienmayxanh.com/...` source page with a bounded
   timeout, a descriptive user agent, retry/backoff, and a low request rate.
3. Parse product-card image attributes, normalize protocol-relative URLs, keep
   only TGDD/DMX CDN HTTP(S) images, deduplicate in document order, and cap the
   group at three.
4. Atomically checkpoint after every group. Resume keeps `ready` groups and
   retries only incomplete groups; `--force` is the sole overwrite path.
5. Persist the production mapping as a versioned group-keyed JSON object under
   `backend/app/catalog_images/data/`, while operational checkpoint/review
   files remain git-ignored under `data/processed/representative-images/`.
6. Select an image with SHA-256 over the SKU and frozen group identity. The
   result is reproducible across processes because Python's randomized
   built-in `hash()` is not used.

## Interface Contract

The mutually exclusive CLI modes are:

```text
python scripts/collect_representative_images.py --pilot --limit-groups 5
python scripts/collect_representative_images.py --all-groups
python scripts/collect_representative_images.py --all-groups --resume  # after interruption
```

The production mapping stores `mapping_version`, `generated_at`, and a
`groups` object keyed by group identity. Each group stores its category,
brand, source URL, constant image type, and up to three URL strings. Status and
failure evidence remain in the operational checkpoint. The selector returns:

```json
{
  "sku": "...",
  "group_key": "38:2",
  "image_url": "https://...",
  "image_type": "representative",
  "mapping_version": 1
}
```

## Data Model

No database or migration change. The reviewed runtime asset is a tracked JSON
file copied into the backend container. Updating the asset changes
`mapping_version`; it never writes `products.image_url`.

## UI / Platform Impact

`POST /api/v1/agent/respond` and the final `done` event from
`/respond/stream` add nullable `image_url`, `image_type`, and
`mapping_version`. The image anchors to the first presented product (or the
first comparison product). When that product has no group mapping the URL is
the shared placeholder and the type remains `representative`. Non-product
turns return null fields and the frontend renders no figure.

The chatbot renders the URL through `SafeImage` and always labels a rendered
figure “Hình ảnh minh họa”. Existing text and comparison rendering are
unchanged.

## Observability

The CLI logs one safe line per group: key, source host, status, and image count.
It never logs cookies, response bodies, local environment values, or image
binary content.

## Alternatives Considered

1. Resolve every SKU through web search. Rejected by the human because exact
   per-product images are no longer required.
2. Use one image per category only. Rejected because brand identity is useful
   and the requested grouping is category plus brand.
3. Use Python `hash(sku) % n`. Rejected because hash randomization makes the
   assignment unstable across processes.
4. Store one URL on every product row. Rejected because the image is group
   representative data, not a verified product fact, and would duplicate the
   same mapping across 8,746 records.
