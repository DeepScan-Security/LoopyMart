from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.cart import CartItem
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User
from app.schemas.order import OrderCreate, OrderItemResponse, OrderResponse

router = APIRouter(prefix="/orders", tags=["orders"])


def _order_to_response(order: Order) -> OrderResponse:
    items = [
        OrderItemResponse(
            id=oi.id,
            product_id=oi.product_id,
            quantity=oi.quantity,
            price_at_order=oi.price_at_order,
            product_name=oi.product.name if oi.product else "",
        )
        for oi in order.items
    ]
    return OrderResponse(
        id=order.id,
        total=order.total,
        status=order.status,
        shipping_address=order.shipping_address,
        items=items,
    )


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    result = await db.execute(
        select(CartItem)
        .where(CartItem.user_id == current_user.id)
        .options(selectinload(CartItem.product))
    )
    cart_items = result.scalars().all()
    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty",
        )
    total = 0.0
    order_items_data: list[tuple[Product, int]] = []
    for ci in cart_items:
        if ci.quantity > ci.product.stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for {ci.product.name}",
            )
        total += ci.product.price * ci.quantity
        order_items_data.append((ci.product, ci.quantity))

    order = Order(
        user_id=current_user.id,
        total=total,
        status="pending",
        shipping_address=data.shipping_address,
    )
    db.add(order)
    await db.flush()
    for product, qty in order_items_data:
        oi = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=qty,
            price_at_order=product.price,
        )
        db.add(oi)
        product.stock -= qty
    for ci in cart_items:
        await db.delete(ci)
    await db.flush()
    await db.refresh(order)
    await db.refresh(order, ["items"])
    for oi in order.items:
        await db.refresh(oi, ["product"])
    return _order_to_response(order)


@router.get("", response_model=list[OrderResponse])
async def list_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[OrderResponse]:
    result = await db.execute(
        select(Order)
        .where(Order.user_id == current_user.id)
        .order_by(Order.id.desc())
        .options(selectinload(Order.items).selectinload(OrderItem.product))
    )
    orders = result.scalars().all()
    return [_order_to_response(o) for o in orders]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id, Order.user_id == current_user.id)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return _order_to_response(order)
