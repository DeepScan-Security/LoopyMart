"""
Orders API routes.
Orders are stored in MongoDB with user_id referencing SQL users.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.cart_mongo import cart_clear, cart_get_by_user
from app.db.orders_mongo import order_create, order_get, order_list_by_user, order_update_status
from app.db.products_mongo import product_decrement_stock, product_get
from app.models.user import User
from app.schemas.order import (
    CreatePaymentResponse,
    OrderCreate,
    OrderItemResponse,
    OrderResponse,
    VerifyPaymentRequest,
)

router = APIRouter(prefix="/orders", tags=["orders"])


def _order_to_response(order: dict) -> OrderResponse:
    """Convert MongoDB order to response schema."""
    items = [
        OrderItemResponse(
            product_id=item["product_id"],
            product_name=item["product_name"],
            quantity=item["quantity"],
            price_at_order=item["price_at_order"],
            product_image_url=item.get("product_image_url"),
        )
        for item in order.get("items", [])
    ]
    
    # Get payment status if available
    payment_status = None
    if order.get("status") == "paid":
        payment_status = "SUCCESS"
    elif order.get("status") == "pending":
        payment_status = "PENDING"
    elif order.get("status") in ["shipped", "delivered"]:
        payment_status = "SUCCESS"
    elif order.get("status") == "cancelled":
        payment_status = "FAILED"
    
    return OrderResponse(
        id=order["id"],
        total=order["total"],
        status=order["status"],
        shipping_address=order["shipping_address"],
        items=items,
        created_at=order.get("created_at").isoformat() if order.get("created_at") else None,
        payment_status=payment_status,
    )


def _ensure_razorpay():
    """Check if Razorpay is configured."""
    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment gateway not configured",
        )


@router.post("/create-payment", response_model=CreatePaymentResponse)
async def create_payment(
    data: OrderCreate,
    current_user: User = Depends(get_current_user),
) -> CreatePaymentResponse:
    """Create order (pending) and Razorpay order; frontend opens Razorpay checkout then calls verify-payment."""
    _ensure_razorpay()
    
    cart_items = await cart_get_by_user(current_user.id)
    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty",
        )
    
    total = 0.0
    order_items: list[dict] = []
    
    for ci in cart_items:
        product = await product_get(ci["product_id"])
        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product no longer available",
            )
        if ci["quantity"] > product["stock"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for {product['name']}",
            )
        total += product["price"] * ci["quantity"]
        order_items.append({
            "product_id": ci["product_id"],
            "product_name": product["name"],
            "quantity": ci["quantity"],
            "price_at_order": product["price"],
            "product_image_url": product.get("image_url"),
        })

    # Create Razorpay order first
    amount_paise = max(settings.min_payment_amount_paise, int(round(total * 100)))
    import razorpay
    client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
    razorpay_order = client.order.create(
        data={
            "amount": amount_paise,
            "currency": "INR",
            "receipt": f"order_{current_user.id}_{len(order_items)}",
        }
    )
    razorpay_order_id = razorpay_order["id"]

    # Create order in MongoDB
    order = await order_create(
        user_id=current_user.id,
        total=total,
        shipping_address=data.shipping_address.model_dump(),
        items=order_items,
        status="pending",
        razorpay_order_id=razorpay_order_id,
    )

    return CreatePaymentResponse(
        order_id=order["id"],
        amount=total,
        amount_paise=amount_paise,
        currency="INR",
        razorpay_order_id=razorpay_order_id,
        key_id=settings.razorpay_key_id,
    )


@router.post("/verify-payment", response_model=OrderResponse)
async def verify_payment(
    data: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user),
) -> OrderResponse:
    """Verify Razorpay signature, then decrement stock, clear cart, mark order paid."""
    _ensure_razorpay()
    
    order = await order_get(data.order_id, user_id=current_user.id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order["status"] != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order already processed",
        )

    import razorpay
    client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": data.razorpay_order_id,
            "razorpay_payment_id": data.razorpay_payment_id,
            "razorpay_signature": data.razorpay_signature,
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment verification failed: {e!s}",
        )

    # Decrement stock for each item
    for item in order.get("items", []):
        await product_decrement_stock(item["product_id"], item["quantity"])
    
    # Clear cart
    await cart_clear(current_user.id)
    
    # Update order status
    updated_order = await order_update_status(
        order["id"],
        status="paid",
        razorpay_payment_id=data.razorpay_payment_id,
    )
    
    return _order_to_response(updated_order)


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreate,
    current_user: User = Depends(get_current_user),
) -> OrderResponse:
    """Create an order without payment (COD or free)."""
    cart_items = await cart_get_by_user(current_user.id)
    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty",
        )
    
    total = 0.0
    order_items: list[dict] = []
    
    for ci in cart_items:
        product = await product_get(ci["product_id"])
        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product no longer available",
            )
        if ci["quantity"] > product["stock"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for {product['name']}",
            )
        total += product["price"] * ci["quantity"]
        order_items.append({
            "product_id": ci["product_id"],
            "product_name": product["name"],
            "quantity": ci["quantity"],
            "price_at_order": product["price"],
            "product_image_url": product.get("image_url"),
        })

    # Create order in MongoDB
    order = await order_create(
        user_id=current_user.id,
        total=total,
        shipping_address=data.shipping_address.model_dump(),
        items=order_items,
        status="pending",
    )

    # Decrement stock for each item
    for item in order_items:
        await product_decrement_stock(item["product_id"], item["quantity"])
    
    # Clear cart
    await cart_clear(current_user.id)

    return _order_to_response(order)


@router.get("", response_model=list[OrderResponse])
async def list_orders(
    current_user: User = Depends(get_current_user),
) -> list[OrderResponse]:
    """List all orders for the current user."""
    orders = await order_list_by_user(current_user.id)
    return [_order_to_response(o) for o in orders]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
) -> OrderResponse:
    """Get a specific order by ID."""
    order = await order_get(order_id, user_id=current_user.id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return _order_to_response(order)
