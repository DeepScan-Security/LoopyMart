"""
Payments API routes (Dummy Implementation).
All payments are simulated - no real payment gateway integration.
"""

import asyncio
import random
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.coupons_mongo import coupon_check_usage, coupon_get_by_code, coupon_mark_used
from app.db.orders_mongo import order_get, order_update_status
from app.db.payments_mongo import payment_create, payment_get_by_order, payment_list_by_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.payment import (
    CouponApplyRequest,
    CouponApplyResponse,
    CouponResponse,
    DummyPaymentRequest,
    DummyPaymentResponse,
    WalletBalanceResponse,
)

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/dummy-pay", response_model=DummyPaymentResponse)
async def process_dummy_payment(
    data: DummyPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DummyPaymentResponse:
    """
    Process a dummy payment (simulated).
    Accepts orderId, amount, paymentMethod, and optional coupon.
    Returns SUCCESS or FAILED (default SUCCESS).
    """
    # Get the order
    order = await order_get(data.order_id, user_id=current_user.id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    
    if order["status"] not in ["pending"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is not in pending status",
        )
    
    # Check if payment already exists
    existing_payment = await payment_get_by_order(data.order_id)
    if existing_payment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment already processed for this order",
        )
    
    # Calculate final amount
    final_amount = data.amount
    coupon_discount = 0.0
    
    # Apply coupon if provided
    if data.coupon_code:
        coupon = await coupon_get_by_code(data.coupon_code)
        if not coupon:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid coupon code",
            )
        
        # Check if user already used this coupon
        already_used = await coupon_check_usage(current_user.id, data.coupon_code)
        if already_used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Coupon already used",
            )
        
        # Check if user is new (no previous paid orders)
        from app.db.orders_mongo import order_list_by_user
        previous_orders = await order_list_by_user(current_user.id)
        paid_orders = [o for o in previous_orders if o["status"] in ["paid", "shipped", "delivered"]]
        
        if len(paid_orders) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Coupons are only available for new users",
            )
        
        coupon_discount = coupon["discount"]
        final_amount = max(0, final_amount - coupon_discount)
        
        # Mark coupon as used
        await coupon_mark_used(current_user.id, data.coupon_code)
    
    # Process wallet payment
    if data.payment_method == "wallet":
        if current_user.wallet_balance < final_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient wallet balance",
            )
        
        # Deduct from wallet atomically
        result = await db.execute(
            select(User).where(User.id == current_user.id).with_for_update()
        )
        user = result.scalar_one()
        
        if user.wallet_balance < final_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient wallet balance",
            )
        
        user.wallet_balance -= final_amount
        await db.commit()
    
    # Simulate payment delay (1-3 seconds)
    await asyncio.sleep(random.uniform(1, 3))
    
    # Simulate payment status (95% success rate)
    payment_status = "SUCCESS" if random.random() < 0.95 else "FAILED"
    
    # Create payment record
    payment = await payment_create(
        order_id=data.order_id,
        user_id=current_user.id,
        amount=final_amount,
        payment_method=data.payment_method,
        status=payment_status,
    )
    
    # Update order status if payment successful
    if payment_status == "SUCCESS":
        await order_update_status(
            data.order_id,
            status="paid",
            user_id=current_user.id,
        )
        
        # Award cashback: fixed ₹50 for first 3 successful paid orders only.
        # Normal max = ₹100 start + ₹50×3 = ₹250, which is intentionally below the
        # ₹333 flag price — players must exploit the race condition to go higher.
        from app.db.orders_mongo import order_list_by_user
        all_orders = await order_list_by_user(current_user.id)
        paid_count = sum(
            1 for o in all_orders
            if o["status"] in ("paid", "shipped", "delivered")
        )
        if paid_count <= 3:
            result = await db.execute(
                select(User).where(User.id == current_user.id).with_for_update()
            )
            user = result.scalar_one()
            user.pending_cashback += 50.0
            await db.commit()
    
    return DummyPaymentResponse(
        payment_id=payment["payment_id"],
        order_id=data.order_id,
        amount=final_amount,
        status=payment_status,
        payment_method=data.payment_method,
    )


@router.get("/wallet/balance", response_model=WalletBalanceResponse)
async def get_wallet_balance(
    current_user: User = Depends(get_current_user),
) -> WalletBalanceResponse:
    """Get current wallet balance."""
    return WalletBalanceResponse(balance=current_user.wallet_balance)


@router.post("/coupon/apply", response_model=CouponApplyResponse)
async def apply_coupon(
    data: CouponApplyRequest,
    current_user: User = Depends(get_current_user),
) -> CouponApplyResponse:
    """Validate a coupon code."""
    coupon = await coupon_get_by_code(data.coupon_code)
    
    if not coupon:
        return CouponApplyResponse(
            coupon_code=data.coupon_code,
            discount=0.0,
            is_valid=False,
            message="Invalid coupon code",
        )
    
    # Check if user already used this coupon
    already_used = await coupon_check_usage(current_user.id, data.coupon_code)
    if already_used:
        return CouponApplyResponse(
            coupon_code=data.coupon_code,
            discount=0.0,
            is_valid=False,
            message="Coupon already used",
        )
    
    # Check if user is new (no previous paid orders)
    from app.db.orders_mongo import order_list_by_user
    previous_orders = await order_list_by_user(current_user.id)
    paid_orders = [o for o in previous_orders if o["status"] in ["paid", "shipped", "delivered"]]
    
    if len(paid_orders) > 0:
        return CouponApplyResponse(
            coupon_code=data.coupon_code,
            discount=0.0,
            is_valid=False,
            message="Coupons are only available for new users",
        )
    
    return CouponApplyResponse(
        coupon_code=data.coupon_code,
        discount=coupon["discount"],
        is_valid=True,
        message=f"Coupon applied! You save ₹{coupon['discount']}",
    )


@router.get("/coupons", response_model=list[CouponResponse])
async def list_coupons(
    current_user: User = Depends(get_current_user),
) -> list[CouponResponse]:
    """List all available coupons with usage status."""
    from app.db.coupons_mongo import coupon_list_all
    
    coupons = await coupon_list_all()
    result = []
    
    for coupon in coupons:
        is_used = await coupon_check_usage(current_user.id, coupon["code"])
        result.append(
            CouponResponse(
                code=coupon["code"],
                discount=coupon["discount"],
                description=coupon["description"],
                is_used=is_used,
            )
        )
    
    return result


@router.get("/history", response_model=list[dict])
async def get_payment_history(
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """Get payment history for current user."""
    payments = await payment_list_by_user(current_user.id)
    return payments
