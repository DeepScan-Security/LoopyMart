"""
Spin the Wheel gamification API routes.
"""

import random
import time
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.flags import get_flag
from app.db.coupons_mongo import coupon_mark_used
from app.db.session import get_db
from app.models.user import User
from app.schemas.spin import SpinResultResponse

router = APIRouter(prefix="/spin", tags=["spin"])

# Daily spin limit
DAILY_SPIN_LIMIT = 5


@router.post("", response_model=SpinResultResponse)
async def spin_wheel(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SpinResultResponse:
    """Spin the wheel to get a reward (up to 5 spins per day)."""
    # Get user with lock
    result = await db.execute(
        select(User).where(User.id == current_user.id).with_for_update()
    )
    user = result.scalar_one()
    
    # Reset counter if it's a new day
    today = date.today()
    if user.last_spin_date != today:
        user.spin_count_today = 0
        user.last_spin_date = today
    
    # Check daily spin limit
    if user.spin_count_today >= DAILY_SPIN_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You have reached your daily limit of {DAILY_SPIN_LIMIT} spins. Come back tomorrow!",
        )
    
    # Weak PRNG: seed with current Unix timestamp (predictable!)
    random.seed(int(time.time()))
    
    # Determine prize (10% mystery, 35% wallet cash, 25% coupon, 30% no reward)
    rand = random.random()
    
    # Increment spin count
    user.spin_count_today += 1
    spins_remaining = DAILY_SPIN_LIMIT - user.spin_count_today
    
    if rand < 0.1:
        # Mystery prize - CTF flag!
        mystery_flag = get_flag("spin_wheel") or "CTF{mystery_prize}"
        
        await db.commit()
        
        return SpinResultResponse(
            prize_type="mystery",
            mystery_flag=mystery_flag,
            message="You found the Mystery Prize! Here's your special reward!",
            spins_remaining=spins_remaining,
        )
    
    elif rand < 0.45:
        # Wallet cash (₹10 to ₹100)
        cash_amount = random.choice([10, 25, 50, 75, 100])
        user.wallet_balance += cash_amount
        
        await db.commit()
        
        return SpinResultResponse(
            prize_type="wallet_cash",
            prize_value=float(cash_amount),
            message=f"Congratulations! You won ₹{cash_amount} wallet cash!",
            spins_remaining=spins_remaining,
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
            
            await db.commit()
            
            return SpinResultResponse(
                prize_type="coupon",
                coupon_code=coupon_code,
                message=f"Congratulations! You won a ₹100 coupon: {coupon_code}",
                spins_remaining=spins_remaining,
            )
        else:
            # All coupons used, give wallet cash instead
            cash_amount = 50
            user.wallet_balance += cash_amount
            
            await db.commit()
            
            return SpinResultResponse(
                prize_type="wallet_cash",
                prize_value=float(cash_amount),
                message=f"Congratulations! You won ₹{cash_amount} wallet cash!",
                spins_remaining=spins_remaining,
            )
    
    else:
        # No reward
        await db.commit()
        
        return SpinResultResponse(
            prize_type="no_reward",
            message="Better luck next time! Keep shopping with us!",
            spins_remaining=spins_remaining,
        )
