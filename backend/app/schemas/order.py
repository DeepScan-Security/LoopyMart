"""Order schemas for API request/response validation."""

from pydantic import BaseModel


class OrderCreate(BaseModel):
    """Schema for creating an order."""
    shipping_address: str


class CreatePaymentResponse(BaseModel):
    """Schema for Razorpay payment creation response."""
    order_id: str  # MongoDB ObjectId as string
    amount: float
    amount_paise: int
    currency: str
    razorpay_order_id: str
    key_id: str


class VerifyPaymentRequest(BaseModel):
    """Schema for verifying Razorpay payment."""
    order_id: str  # MongoDB ObjectId as string
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class OrderItemResponse(BaseModel):
    """Schema for order item in response."""
    product_id: str
    product_name: str
    quantity: int
    price_at_order: float
    product_image_url: str | None = None

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Schema for order response (MongoDB)."""
    id: str  # MongoDB ObjectId as string
    total: float
    status: str
    shipping_address: str
    items: list[OrderItemResponse] = []
    created_at: str | None = None
    payment_status: str | None = None

    class Config:
        from_attributes = True


class AdminOrderResponse(BaseModel):
    """Order with user info for admin dashboard (MongoDB)."""
    id: str  # MongoDB ObjectId as string
    user_id: int
    user_email: str
    user_name: str
    total: float
    status: str
    shipping_address: str
    items: list[OrderItemResponse] = []

    class Config:
        from_attributes = True


OrderResponse.model_rebuild()
