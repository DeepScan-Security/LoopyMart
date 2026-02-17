"""Wallet schemas for API request/response validation."""

from pydantic import BaseModel


class WalletResponse(BaseModel):
    """Schema for wallet info response."""
    balance: float
    pending_cashback: float


class RedeemResponse(BaseModel):
    """Schema for cashback redemption response."""
    success: bool
    amount_redeemed: float
    new_balance: float
    message: str


class FlagStoreItem(BaseModel):
    """Schema for flag store item."""
    id: str
    name: str
    price: float
    description: str


class FlagStoreResponse(BaseModel):
    """Schema for flag store listing response."""
    items: list[FlagStoreItem]


class PurchaseRequest(BaseModel):
    """Schema for purchase request."""
    item_id: str


class PurchaseResponse(BaseModel):
    """Schema for purchase response."""
    success: bool
    flag: str | None = None
    message: str
    new_balance: float | None = None
