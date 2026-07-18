"""Product Catalog API.

Read-only HTTP access to the product catalog stored in PostgreSQL. Agents and
frontends call this API; they do not talk to PostgreSQL directly.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from backend.app.api.errors import register_error_handlers
from backend.app.api.routes import brands, categories, health, products
from backend.app.config.db_settings import load_data_platform_settings

API_DESCRIPTION = """
Read-only Product Catalog API over the provided Điện Máy XANH dataset
(14 categories, 8,746 products). Product attributes are returned verbatim.

Intended tool surface for agents:
`list_categories`, `list_brands`, `list_category_attributes`,
`search_products`, `get_product_detail`, `compare_products`.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = load_data_platform_settings()
    pool = ConnectionPool(
        settings.conninfo(),
        min_size=1,
        max_size=10,
        kwargs={"autocommit": True, "row_factory": dict_row},
        open=False,
    )
    pool.open(wait=True, timeout=10)
    app.state.pool = pool
    try:
        yield
    finally:
        pool.close()


app = FastAPI(
    title="Product Catalog API",
    version="0.1.0",
    description=API_DESCRIPTION,
    lifespan=lifespan,
)

_cors_origins = load_data_platform_settings().cors_origins()
if _cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

register_error_handlers(app)
app.include_router(health.router)
app.include_router(categories.router)
app.include_router(brands.router)
app.include_router(products.router)
