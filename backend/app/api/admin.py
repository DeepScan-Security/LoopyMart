"""
Admin API routes.
Categories, products, and orders management.
All data stored in MongoDB except user lookup in PostgreSQL.
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.config import settings
from app.db.categories_mongo import (
    category_create,
    category_delete,
    category_exists,
    category_get,
    category_update,
)
from app.db.orders_mongo import order_list_all
from app.db.products_mongo import product_create, product_delete, product_update
from app.db.session import get_db
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.schemas.order import AdminOrderResponse, OrderItemResponse
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate

router = APIRouter(prefix="/admin", tags=["admin"])


def get_upload_dir() -> Path:
    """Get the upload directory path from config."""
    return Path(__file__).resolve().parent.parent.parent / settings.uploads_dir


ALLOWED_EXTENSIONS = {"image/jpeg", "image/png", "image/webp", "image/gif"}


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_category(
    data: CategoryCreate,
    current_user: User = Depends(require_admin),
) -> CategoryResponse:
    """Create a new category."""
    if await category_exists(data.slug):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category slug already exists",
        )
    category = await category_create(
        name=data.name,
        slug=data.slug,
        description=data.description,
        image_url=data.image_url,
    )
    return CategoryResponse(**category)


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def admin_update_category(
    category_id: str,
    data: CategoryUpdate,
    current_user: User = Depends(require_admin),
) -> CategoryResponse:
    """Update an existing category."""
    category = await category_get(category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    # Check if new slug conflicts with another category
    if data.slug and data.slug != category["slug"]:
        if await category_exists(data.slug):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category slug already exists",
            )
    
    updated = await category_update(
        category_id,
        name=data.name,
        slug=data.slug,
        description=data.description,
        image_url=data.image_url,
    )
    return CategoryResponse(**updated)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_category(
    category_id: str,
    current_user: User = Depends(require_admin),
) -> None:
    """Delete a category."""
    deleted = await category_delete(category_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_product(
    data: ProductCreate,
    current_user: User = Depends(require_admin),
) -> ProductResponse:
    """Create a new product."""
    category = await category_get(data.category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found",
        )
    product = await product_create(
        name=data.name,
        description=data.description,
        price=data.price,
        image_url=data.image_url,
        stock=data.stock,
        category_id=data.category_id,
    )
    return ProductResponse(**product)


@router.put("/products/{product_id}", response_model=ProductResponse)
async def admin_update_product(
    product_id: str,
    data: ProductUpdate,
    current_user: User = Depends(require_admin),
) -> ProductResponse:
    """Update an existing product."""
    if data.category_id is not None:
        category = await category_get(data.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found",
            )
    product = await product_update(
        product_id,
        name=data.name,
        description=data.description,
        price=data.price,
        image_url=data.image_url,
        stock=data.stock,
        category_id=data.category_id,
    )
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return ProductResponse(**product)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_product(
    product_id: str,
    current_user: User = Depends(require_admin),
) -> None:
    """Delete a product."""
    deleted = await product_delete(product_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")


@router.post("/upload")
async def admin_upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
) -> dict:
    """Upload an image file."""
    if file.content_type not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Allowed types: jpeg, png, webp, gif",
        )
    
    upload_dir = get_upload_dir()
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    ext = Path(file.filename or "img").suffix or ".png"
    name = f"{uuid.uuid4().hex}{ext}"
    path = upload_dir / name
    
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large (max 5MB)",
        )
    
    path.write_bytes(content)
    # #region agent log
    import json as _json_debug
    _debug_upload_data = {"location": "admin.py:upload_image", "message": "File uploaded", "data": {"saved_path": str(path), "path_exists": path.exists(), "file_size": len(content), "returned_url": f"/static/uploads/{name}"}, "timestamp": __import__("time").time() * 1000, "sessionId": "debug-session", "hypothesisId": "H3"}
    with open("/Users/shubham2201/Documents/Projects/Flipkart-clone/.cursor/debug.log", "a") as _f: _f.write(_json_debug.dumps(_debug_upload_data) + "\n")
    # #endregion
    return {"url": f"/static/uploads/{name}"}


def _order_to_admin_response(order: dict, user_email: str = "", user_name: str = "") -> AdminOrderResponse:
    """Convert MongoDB order to admin response schema."""
    items = [
        OrderItemResponse(
            product_id=item["product_id"],
            product_name=item["product_name"],
            quantity=item["quantity"],
            price_at_order=item["price_at_order"],
        )
        for item in order.get("items", [])
    ]
    return AdminOrderResponse(
        id=order["id"],
        user_id=order["user_id"],
        user_email=user_email,
        user_name=user_name,
        total=order["total"],
        status=order["status"],
        shipping_address=order["shipping_address"],
        items=items,
    )


@router.get("/orders", response_model=list[AdminOrderResponse])
async def admin_list_all_orders(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminOrderResponse]:
    """List all orders from all users (admin only)."""
    orders = await order_list_all()
    
    # Get unique user IDs
    user_ids = list(set(o["user_id"] for o in orders))
    
    # Batch fetch user info
    user_map = {}
    if user_ids:
        result = await db.execute(
            select(User).where(User.id.in_(user_ids))
        )
        for user in result.scalars().all():
            user_map[user.id] = {"email": user.email, "name": user.full_name}
    
    return [
        _order_to_admin_response(
            o,
            user_email=user_map.get(o["user_id"], {}).get("email", ""),
            user_name=user_map.get(o["user_id"], {}).get("name", ""),
        )
        for o in orders
    ]
