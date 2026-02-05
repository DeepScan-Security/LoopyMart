"""
Spin the Wheel gamification API routes.
"""

import random
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.coupons_mongo import coupon_mark_used
from app.db.session import get_db
from app.models.user import User
from app.schemas.spin import SpinResultResponse

router = APIRouter(prefix="/spin", tags=["spin"])


@router.post("", response_model=SpinResultResponse)
async def spin_wheel(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SpinResultResponse:
    """Spin the wheel to get a reward (can only spin once)."""
    # Check if user has already spun
    if current_user.has_spun_wheel:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already spun the wheel. Each user can only spin once.",
        )
    
    # Get user with lock
    result = await db.execute(
        select(User).where(User.id == current_user.id).with_for_update()
    )
    user = result.scalar_one()
    
    if user.has_spun_wheel:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already spun the wheel. Each user can only spin once.",
        )
    
    # Determine prize (40% wallet cash, 30% coupon, 30% no reward)
    rand = random.random()
    
    if rand < 0.4:
        # Wallet cash (₹10 to ₹100)
        cash_amount = random.choice([10, 25, 50, 75, 100])
        user.wallet_balance += cash_amount
        user.has_spun_wheel = True
        
        await db.commit()
        
        return SpinResultResponse(
            prize_type="wallet_cash",
            prize_value=float(cash_amount),
            message=f"Congratulations! You won ₹{cash_amount} wallet cash!",
        )
    
    elif rand < 0.7:
        # Coupon (one of the default coupons)
        coupon_codes = ["WELCOME100", "SAVE100", "FIRSTBUY100", "NEWUSER100"]
        
        # Check which coupons user hasn't used yet
        from app.db.coupons_mongo import coupon_check_usage
        available_coupons = []
        for code in coupon_codes:
            is_used = await coupon_check_usage(user.id, code)
            if not is_used:
                available_coupons.append(code)
        
        if available_coupons:
            # Give a random available coupon
            coupon_code = random.choice(available_coupons)
            await coupon_mark_used(user.id, coupon_code)
            user.has_spun_wheel = True
            
            await db.commit()
            
            return SpinResultResponse(
                prize_type="coupon",
                coupon_code=coupon_code,
                message=f"Congratulations! You won a ₹100 coupon: {coupon_code}",
            )
        else:
            # All coupons used, give wallet cash instead
            cash_amount = 50
            user.wallet_balance += cash_amount
            user.has_spun_wheel = True
            
            await db.commit()
            
            return SpinResultResponse(
                prize_type="wallet_cash",
                prize_value=float(cash_amount),
                message=f"Congratulations! You won ₹{cash_amount} wallet cash!",
            )
    
    else:
        # No reward
        user.has_spun_wheel = True
        
        await db.commit()
        
        return SpinResultResponse(
            prize_type="no_reward",
            message="Better luck next time! Keep shopping with us!",
        )
