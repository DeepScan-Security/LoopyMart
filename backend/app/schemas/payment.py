"""Payment schemas for API request/response validation."""

from pydantic import BaseModel


class DummyPaymentRequest(BaseModel):
    """Schema for creating a dummy payment."""
    order_id: str
    amount: float
    payment_method: str  # "wallet", "card", "upi", "cod"
    coupon_code: str | None = None


class DummyPaymentResponse(BaseModel):
    """Schema for dummy payment response."""
    payment_id: str
    order_id: str
    amount: float
    status: str  # "SUCCESS" or "FAILED"
    payment_method: str


class WalletBalanceResponse(BaseModel):
    """Schema for wallet balance response."""
    balance: float


class CouponResponse(BaseModel):
    """Schema for coupon response."""
    code: str
    discount: float
    description: str
    is_used: bool = False


class CouponApplyRequest(BaseModel):
    """Schema for applying coupon."""
    coupon_code: str


class CouponApplyResponse(BaseModel):
    """Schema for coupon application response."""
    coupon_code: str
    discount: float
    is_valid: bool
    message: str
