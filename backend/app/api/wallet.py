"""
Wallet & Rewards API routes.

CTF Challenge: Race Condition vulnerability in cashback redemption.
The redeem endpoint intentionally lacks proper locking, allowing
concurrent requests to double-credit the wallet balance.
"""

import asyncio
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.flags import get_flag
from app.db.session import get_db
from app.models.user import User
from app.schemas.wallet import (
    FlagStoreItem,
    FlagStoreResponse,
    PurchaseRequest,
    PurchaseResponse,
    RedeemResponse,
    WalletResponse,
)

router = APIRouter(prefix="/wallet", tags=["wallet"])

# Flag store items
FLAG_STORE_ITEMS = [
    FlagStoreItem(
        id="ctf_flag",
        name="Flag",
        price=333.0,
        description="A mysterious flag that holds secrets. Can you afford it?",
    ),
]


@router.get("", response_model=WalletResponse)
async def get_wallet(
    current_user: User = Depends(get_current_user),
) -> WalletResponse:
    """Get current wallet balance and pending cashback."""
    return WalletResponse(
        balance=current_user.wallet_balance,
        pending_cashback=current_user.pending_cashback,
    )


@router.post("/redeem", response_model=RedeemResponse)
async def redeem_cashback(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RedeemResponse:

    result = await db.execute(
        select(User).where(User.id == current_user.id)
    )
    user = result.scalar_one()

    # Compute effective daily count in pure Python — do NOT assign to ORM
    # attributes here, as that marks the session dirty and causes SQLAlchemy
    # to auto-flush a row-locking UPDATE on the first db.commit(), which would
    # serialize concurrent requests and kill the intended race condition window.
    today = date.today()
    is_new_day = user.last_cashback_redeem_date != today
    effective_count = 0 if is_new_day else user.redeem_count_today

    # Check daily redemption limit (3 per day)
    DAILY_REDEEM_LIMIT = 3
    if effective_count >= DAILY_REDEEM_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You can only redeem cashback {DAILY_REDEEM_LIMIT} times per day. Try again tomorrow!",
        )

    # Check if there's cashback to redeem
    if user.pending_cashback <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending cashback to redeem",
        )
    

    amount = user.pending_cashback

    # VULNERABLE: Artificial delay widens the race condition window
    # This gives attackers time to send concurrent requests
    await asyncio.sleep(0.1)

    # STEP 3: Increment balance with wallet_balance + :amount (not a pre-computed SET).
    # VULNERABLE: Because the pending_cashback > 0 check and this write are in
    # separate transactions, N concurrent requests all pass the check before any
    # of them zeros out pending_cashback. Each then genuinely adds :amount to the
    # current DB value, so N winners each contribute +amount — multiplying the
    # effective cashback far beyond a single honest redeem.
    await db.execute(
        text("UPDATE users SET wallet_balance = wallet_balance + :amount WHERE id = :id"),
        {"amount": amount, "id": user.id}
    )
    await db.commit()
    
    # STEP 4: Mark as used SEPARATELY after balance update
    # VULNERABLE: This creates the TOCTOU window - other requests can still
    # see pending_cashback > 0 and pass the check before this executes
    await db.execute(
        text("UPDATE users SET pending_cashback = 0 WHERE id = :id"),
        {"id": user.id}
    )
    await db.commit()
    
    # STEP 5: Update last redeem date and counter atomically in SQL.
    # If it's a new day, reset counter to 1; otherwise increment.
    # Never touch ORM attributes — keeps the session clean and
    # preserves the race condition window above.
    if is_new_day:
        await db.execute(
            text("UPDATE users SET last_cashback_redeem_date = :today, redeem_count_today = 1 WHERE id = :id"),
            {"today": today, "id": user.id}
        )
    else:
        await db.execute(
            text("UPDATE users SET redeem_count_today = redeem_count_today + 1 WHERE id = :id"),
            {"id": user.id}
        )
    await db.commit()
    
    # Re-fetch to get the final balance for response
    result = await db.execute(
        select(User).where(User.id == current_user.id)
    )
    user = result.scalar_one()
    
    return RedeemResponse(
        success=True,
        amount_redeemed=amount,
        new_balance=user.wallet_balance,
        message=f"Successfully redeemed ₹{amount:.2f} cashback!",
    )


@router.get("/flag-store", response_model=FlagStoreResponse)
async def get_flag_store(
    current_user: User = Depends(get_current_user),
) -> FlagStoreResponse:
    """Get list of items available in the flag store."""
    return FlagStoreResponse(items=FLAG_STORE_ITEMS)


@router.post("/purchase-flag", response_model=PurchaseResponse, response_model_exclude_unset=True)
async def purchase_flag(
    data: PurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PurchaseResponse:
    """
    Purchase an item from the flag store.
    The CTF flag costs ₹333. Normal path tops out at ₹250 (₹100 start + ₹50×3 orders).
    Players must exploit the race condition in POST /wallet/redeem to push their balance above ₹333.
    """
    # Find the item
    item = next((i for i in FLAG_STORE_ITEMS if i.id == data.item_id), None)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found in flag store",
        )
    
    # Get user with lock for purchase (this part is safe)
    result = await db.execute(
        select(User).where(User.id == current_user.id).with_for_update()
    )
    user = result.scalar_one()
    
    # Check balance
    if user.wallet_balance < item.price:
        return PurchaseResponse(
            success=False,
            message=f"Insufficient balance. You need ₹{item.price:.2f} but have ₹{user.wallet_balance:.2f}",
            new_balance=user.wallet_balance,
        )
    
    # Deduct balance
    user.wallet_balance -= item.price
    await db.commit()
    
    # Return the CTF flag only when visible; omit the field entirely when hidden.
    flag = get_flag("wallet_race")
    purchase = PurchaseResponse(
        success=True,
        message="Congratulations! You've discovered the secret!",
        new_balance=user.wallet_balance,
    )
    if flag:
        purchase.flag = flag
    return purchase
