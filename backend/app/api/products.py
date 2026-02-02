"""
Products API routes.
Products are stored in MongoDB.
"""

from fastapi import APIRouter, HTTPException, Query, status

from app.core.config import settings
from app.db.categories_mongo import category_get_by_slug
from app.db.products_mongo import product_get, product_list
from app.schemas.product import ProductResponse

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductResponse])
async def list_products(
    category_id: str | None = Query(None),
    category_slug: str | None = Query(None),
    q: str | None = Query(None, description="Search by product name"),
    search: str | None = Query(None, description="Search by product name (alias for q)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(default=None, ge=1, le=None),
) -> list[ProductResponse]:
    """List products with optional filtering by category and search."""
    # Use config values for defaults
    if limit is None:
        limit = settings.api_products_default_limit
    limit = min(limit, settings.api_products_max_limit)
    
    # Support both q and search; use non-empty value so filter is applied
    raw_search = search if search is not None else q
    search_term = (raw_search or "").strip() or None
    
    cat_id = category_id
    if category_slug is not None:
        category = await category_get_by_slug(category_slug)
        if category is None:
            return []
        cat_id = category["id"]
    
    products_data = await product_list(
        category_id=cat_id,
        search=search_term,
        skip=skip,
        limit=limit,
    )
    return [ProductResponse(**p) for p in products_data]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str) -> ProductResponse:
    """Get a single product by ID."""
    product = await product_get(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return ProductResponse(**product)
