"""Single-product detail view over the preserved original attributes."""

from dataclasses import dataclass

from backend.app.agent.catalog.dataset_adapter import GenericProduct


@dataclass(frozen=True, slots=True)
class ProductDetail:
    product: GenericProduct
    attributes: dict[str, str]


def product_detail(
    products: list[GenericProduct], productidweb: str
) -> ProductDetail | None:
    for product in products:
        if product.productidweb == productidweb:
            attributes = {
                key: str(value).strip()
                for key, value in product.attributes.items()
                if value not in (None, "")
            }
            return ProductDetail(product=product, attributes=attributes)
    return None
