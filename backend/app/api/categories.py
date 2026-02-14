"""
Categories API routes.
Categories are stored in MongoDB.
"""

from fastapi import APIRouter, HTTPException, status

from app.db.categories_mongo import category_get_by_slug, category_list
from app.schemas.category import CategoryResponse

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
async def list_categories() -> list[CategoryResponse]:
    """List all categories."""
    categories = await category_list()
    return [CategoryResponse(**c) for c in categories]


@router.get("/{slug}", response_model=CategoryResponse)
async def get_category_by_slug(slug: str) -> CategoryResponse:
    """Get a category by its slug."""
    category = await category_get_by_slug(slug)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return CategoryResponse(**category)
