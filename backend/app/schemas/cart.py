"""Cart schemas for API request/response validation."""

from pydantic import BaseModel


class CartItemCreate(BaseModel):
    """Schema for adding an item to cart."""
    product_id: str  # MongoDB ObjectId string
    quantity: int = 1


class CartItemUpdate(BaseModel):
    """Schema for updating cart item quantity."""
    quantity: int


class CartItemResponse(BaseModel):
    """Schema for cart item response (MongoDB)."""
    id: str  # MongoDB ObjectId as string
    product_id: str
    quantity: int
    product_name: str
    product_price: float
    product_image_url: str | None
    product_stock: int

    class Config:
        from_attributes = True
