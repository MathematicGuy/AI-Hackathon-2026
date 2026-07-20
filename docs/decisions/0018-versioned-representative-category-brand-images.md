# 0018 Versioned Representative Category-Brand Images

Date: 2026-07-19

## Status

Accepted

## Context

The real catalog has 8,746 product rows but no verified per-product image
source. A five-group pilot proved that official Điện Máy Xanh category-brand
pages can provide useful representative images without general web search or
product-level identity resolution. The product owner accepted representative,
not exact-SKU, imagery and requires the chatbot to disclose that distinction.

## Decision

1. Store representative imagery once per category-brand group in a versioned,
   tracked JSON runtime asset. Do not add or populate a product image column.
2. A group has at most three unique URLs, all validated against the official
   TGDD/DMX CDN allowlist. Operational statuses and failures stay in a separate
   checkpoint/review artifact.
3. Select one URL with SHA-256 over the frozen group key and SKU. The selection
   is deterministic across processes and mapping reads.
4. Agent product turns expose nullable `image_url`, `image_type`, and
   `mapping_version`. The first presented product is the image anchor. When its
   group is unmapped, use a common local placeholder and keep
   `image_type="representative"`; turns without a product return null fields.
5. The chatbot renders an image only when `image_url` is present and labels it
   “Hình ảnh minh họa”. It must not imply an exact SKU photo.
6. Full collection requires an explicit `--all-groups` flag, uses conservative
   rate limiting, checkpoints every group, and preserves ready groups unless
   `--force` is also explicit.

## Alternatives Considered

1. Resolve and store an exact image for all SKUs — rejected because available
   identifiers do not provide reliable one-to-one web identity and the human
   explicitly removed this requirement.
2. Duplicate the selected representative URL into every product row — rejected
   because it turns group presentation data into a false product fact and adds
   unnecessary catalog writes.
3. Return an image list for every product in a reply — deferred; the requested
   additive API is singular and the chatbot currently renders one figure per
   assistant message.

## Consequences

Positive:

- One compact mapping serves the whole catalog without database mutation.
- The same SKU remains visually stable while the mapping version is frozen.
- Missing and obsolete groups degrade to an explicit placeholder.

Tradeoffs:

- A representative image is not an exact product photo and must always be
  disclosed as illustrative.
- Listing-page markup and category slugs are external dependencies; checkpoint
  evidence and allowlists contain their failure surface.
- Updating the reviewed mapping requires a version bump and application
  deployment.

## Follow-Up

- Review the first intentional all-groups crawl before bumping the tracked
  mapping beyond version 1.
- Add per-product image arrays only through a separate API decision if the UI
  later needs one image for every compared item.
