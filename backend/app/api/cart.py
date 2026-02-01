from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.cart import CartItem
from app.models.product import Product
from app.models.user import User
from app.schemas.cart import CartItemCreate, CartItemResponse, CartItemUpdate

router = APIRouter(prefix="/cart", tags=["cart"])


def _cart_item_to_response(item: CartItem) -> CartItemResponse:
    return CartItemResponse(
        id=item.id,
        product_id=item.product_id,
        quantity=item.quantity,
        product_name=item.product.name,
        product_price=item.product.price,
        product_image_url=item.product.image_url,
        product_stock=item.product.stock,
    )


@router.get("", response_model=list[CartItemResponse])
async def get_cart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CartItemResponse]:
    result = await db.execute(
        select(CartItem)
        .where(CartItem.user_id == current_user.id)
        .options(selectinload(CartItem.product))
    )
    items = result.scalars().all()
    return [_cart_item_to_response(i) for i in items]


@router.post("", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    data: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CartItemResponse:
    result = await db.execute(select(Product).where(Product.id == data.product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if product.stock < data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient stock",
        )
    existing = await db.execute(
        select(CartItem).where(
            CartItem.user_id == current_user.id,
            CartItem.product_id == data.product_id,
        )
    )
    cart_item = existing.scalar_one_or_none()
    if cart_item:
        cart_item.quantity += data.quantity
        if cart_item.quantity > product.stock:
            cart_item.quantity = product.stock
        await db.flush()
        await db.refresh(cart_item)
        await db.refresh(cart_item, ["product"])
    else:
        cart_item = CartItem(
            user_id=current_user.id,
            product_id=data.product_id,
            quantity=data.quantity,
        )
        db.add(cart_item)
        await db.flush()
        await db.refresh(cart_item)
        await db.refresh(cart_item, ["product"])
    return _cart_item_to_response(cart_item)


@router.patch("/{item_id}", response_model=CartItemResponse)
async def update_cart_item(
    item_id: int,
    data: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CartItemResponse:
    result = await db.execute(
        select(CartItem)
        .where(CartItem.id == item_id, CartItem.user_id == current_user.id)
        .options(selectinload(CartItem.product))
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    if data.quantity <= 0:
        await db.delete(item)
        await db.flush()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Use DELETE to remove")
    item.quantity = min(data.quantity, item.product.stock)
    await db.flush()
    await db.refresh(item)
    return _cart_item_to_response(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_cart_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(CartItem).where(CartItem.id == item_id, CartItem.user_id == current_user.id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    await db.delete(item)
    await db.flush()
