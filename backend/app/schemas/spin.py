"""Spin the Wheel schemas for API request/response validation."""

from pydantic import BaseModel


class SpinResultResponse(BaseModel):
    """Schema for spin the wheel result."""
    prize_type: str  # "wallet_cash", "coupon", "no_reward"
    prize_value: float | None = None
    coupon_code: str | None = None
    message: str
