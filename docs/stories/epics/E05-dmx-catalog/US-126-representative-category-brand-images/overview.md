# US-126 Representative Category-Brand Images

## Current Behavior

The five-group pilot is complete: each configured category-brand group has
three reviewed first-party image URLs and the SHA-256 selector is stable. The
promoted implementation now ships explicit pilot/all-group collection modes,
a versioned runtime mapping seeded from those five groups, additive Agent API
fields, a shared placeholder, and disclosed chatbot rendering. The all-group
resume crawl has now completed with a first-party DMX search fallback for
groups whose direct listing page had no exact-brand product cards.

## Target Behavior

A deliberately gated collector supports either the existing five-group pilot
or all valid category-brand groups derived from the catalog. It keeps at most
three official TGDD/DMX CDN URLs per group and writes a versioned production
mapping without downloading images or updating the database.

The Agent API selects an image for the first product presented in a turn by
hashing that product's SKU against its group. Product turns with no mapping use
one shared local placeholder; turns with no product carry no image. The
chatbot renders the image with the disclosure “Hình ảnh minh họa”.

## Affected Users

- Catalog and storefront maintainers reviewing representative imagery.
- Customers who may later see category-brand representative images in product
  cards when exact product imagery is unavailable.

## Affected Product Docs

- `docs/product/dmx-catalog-api.md` remains unchanged because no catalog row or
  catalog endpoint is modified.
- `docs/product/architecture/multi-category-agent.md` records the additive
  Agent API image projection and chatbot rendering behavior.
- `docs/decisions/0018-versioned-representative-category-brand-images.md`
  records the durable mapping and fallback boundary.

## Non-Goals

- Resolving images for individual SKUs or `productidweb` values.
- Brave, Google, or another general web-search provider.
- Downloading image binaries.
- Updating PostgreSQL, migrations, or 8,746 product records.
- Claiming that a representative image is the exact photographed SKU.
- Adding an image to policy, small-talk, clarification, or other turns that do
  not present a product.
