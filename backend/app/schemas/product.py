"""Product schemas for API request/response validation."""

from pydantic import BaseModel


class ProductBase(BaseModel):
    """Base product schema with common fields."""
    name: str
    description: str | None = None
    price: float
    image_url: str | None = None
    stock: int = 0
    category_id: str  # MongoDB ObjectId as string


class ProductCreate(ProductBase):
    """Schema for creating a new product."""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    name: str | None = None
    description: str | None = None
    price: float | None = None
    image_url: str | None = None
    stock: int | None = None
    category_id: str | None = None


class ProductResponse(ProductBase):
    """Schema for product response (MongoDB)."""
    id: str  # MongoDB ObjectId string

    class Config:
        from_attributes = True


class ProductWithCategory(ProductResponse):
    """Product response with category name."""
    category_name: str | None = None
