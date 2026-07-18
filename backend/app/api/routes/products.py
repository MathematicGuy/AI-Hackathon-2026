from fastapi import APIRouter, Depends

from backend.app.api.deps import get_service
from backend.app.api.schemas.catalog import (
    BatchRequest,
    BatchResponse,
    CompareRequest,
    CompareResponse,
    ProductRecord,
    SearchRequest,
    SearchResponse,
)
from backend.app.api.schemas.common import ErrorResponse
from backend.app.services.catalog_service import CatalogService

router = APIRouter(prefix="/api/v1", tags=["products"])


@router.get(
    "/products/{sku}",
    response_model=ProductRecord,
    responses={404: {"model": ErrorResponse}},
)
def get_product(sku: str, service: CatalogService = Depends(get_service)) -> dict:
    """Full product detail by SKU (the primary identifier)."""
    return service.get_product(sku)


@router.post(
    "/products/search",
    response_model=SearchResponse,
    responses={422: {"model": ErrorResponse}},
)
def search_products(
    request: SearchRequest, service: CatalogService = Depends(get_service)
) -> dict:
    """Search products by query, category, brands, and attribute filters."""
    items, total, total_pages = service.search(request)
    return {
        "items": items,
        "page": request.page,
        "page_size": request.page_size,
        "total": total,
        "total_pages": total_pages,
    }


@router.post(
    "/products/batch",
    response_model=BatchResponse,
    responses={422: {"model": ErrorResponse}},
)
def batch_products(
    request: BatchRequest, service: CatalogService = Depends(get_service)
) -> dict:
    """Fetch many products by SKU in one call (max 100)."""
    items, missing = service.batch(request.skus)
    return {"items": items, "missing_skus": missing}


@router.post(
    "/products/compare",
    response_model=CompareResponse,
    responses={422: {"model": ErrorResponse}},
)
def compare_products(
    request: CompareRequest, service: CatalogService = Depends(get_service)
) -> dict:
    """Compare up to 5 products (same category preferred)."""
    products, same_category, category_code, attributes, warnings = service.compare(
        request.skus
    )
    return {
        "products": products,
        "same_category": same_category,
        "category_code": category_code,
        "attributes": attributes,
        "warnings": warnings,
    }
