"""
Cart API routes.
Cart items are stored in MongoDB with user_id referencing SQL users.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.db.cart_mongo import (
    cart_add_item,
    cart_get_by_user,
    cart_get_item_by_id,
    cart_remove_item,
    cart_set_quantity,
)
from app.db.products_mongo import product_get
from app.models.user import User
from app.schemas.cart import CartItemCreate, CartItemResponse, CartItemUpdate

router = APIRouter(prefix="/cart", tags=["cart"])


async def _cart_item_to_response(item: dict) -> CartItemResponse:
    """Convert MongoDB cart item to response schema with product details."""
    product = await product_get(item["product_id"])
    if product:
        return CartItemResponse(
            id=item["id"],
            product_id=item["product_id"],
            quantity=item["quantity"],
            product_name=product["name"],
            product_price=product["price"],
            product_image_url=product.get("image_url"),
            product_stock=product["stock"],
        )
    return CartItemResponse(
        id=item["id"],
        product_id=item["product_id"],
        quantity=item["quantity"],
        product_name="(Unavailable)",
        product_price=0.0,
        product_image_url=None,
        product_stock=0,
    )


@router.get("", response_model=list[CartItemResponse])
async def get_cart(
    current_user: User = Depends(get_current_user),
) -> list[CartItemResponse]:
    """Get all cart items for the current user."""
    items = await cart_get_by_user(current_user.id)
    return [await _cart_item_to_response(item) for item in items]


@router.post("", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    data: CartItemCreate,
    current_user: User = Depends(get_current_user),
) -> CartItemResponse:
    """Add a product to the cart."""
    product = await product_get(data.product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if product["stock"] < data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient stock",
        )
    cart_item = await cart_add_item(current_user.id, data.product_id, data.quantity)
    
    # Ensure quantity doesn't exceed stock
    if cart_item["quantity"] > product["stock"]:
        cart_item = await cart_set_quantity(cart_item["id"], current_user.id, product["stock"])
    
    return await _cart_item_to_response(cart_item)


@router.patch("/{item_id}", response_model=CartItemResponse)
async def update_cart_item(
    item_id: str,
    data: CartItemUpdate,
    current_user: User = Depends(get_current_user),
) -> CartItemResponse:
    """Update cart item quantity."""
    item = await cart_get_item_by_id(item_id, current_user.id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    
    if data.quantity <= 0:
        await cart_remove_item(item_id, current_user.id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Use DELETE to remove")
    
    product = await product_get(item["product_id"])
    max_qty = product["stock"] if product else 0
    new_quantity = min(data.quantity, max_qty)
    
    updated_item = await cart_set_quantity(item_id, current_user.id, new_quantity)
    if not updated_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    
    return await _cart_item_to_response(updated_item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_cart_item(
    item_id: str,
    current_user: User = Depends(get_current_user),
) -> None:
    """Remove an item from the cart."""
    removed = await cart_remove_item(item_id, current_user.id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
