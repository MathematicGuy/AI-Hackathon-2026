"""Representative catalog image collection and assignment."""

from backend.app.catalog_images.representative import (
    PILOT_GROUPS,
    GroupSource,
    assign_representative_image,
    collect_group,
    group_key,
    normalize_image_url,
    normalized_brand_slug,
    parse_representative_images,
    validate_source_url,
)
from backend.app.catalog_images.mapping import (
    PLACEHOLDER_IMAGE_URL,
    RepresentativeImageMapping,
    load_default_mapping,
)
from backend.app.catalog_images.sources import catalog_group_sources, source_for_group

__all__ = [
    "PILOT_GROUPS",
    "GroupSource",
    "assign_representative_image",
    "collect_group",
    "group_key",
    "normalize_image_url",
    "normalized_brand_slug",
    "parse_representative_images",
    "validate_source_url",
    "PLACEHOLDER_IMAGE_URL",
    "RepresentativeImageMapping",
    "load_default_mapping",
    "catalog_group_sources",
    "source_for_group",
]
