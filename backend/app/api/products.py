from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.category import Category
from app.models.product import Product
from app.schemas.product import ProductResponse

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductResponse])
async def list_products(
    db: AsyncSession = Depends(get_db),
    category_id: int | None = Query(None),
    category_slug: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[ProductResponse]:
    q = select(Product).order_by(Product.id)
    if category_id is not None:
        q = q.where(Product.category_id == category_id)
    if category_slug is not None:
        subq = select(Category.id).where(Category.slug == category_slug)
        result_cat = await db.execute(subq)
        cat_id = result_cat.scalar_one_or_none()
        if cat_id is None:
            return []
        q = q.where(Product.category_id == cat_id)
    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    products = result.scalars().all()
    return [ProductResponse.model_validate(p) for p in products]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
) -> ProductResponse:
    result = await db.execute(
        select(Product).where(Product.id == product_id).options(selectinload(Product.category))
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return ProductResponse.model_validate(product)
