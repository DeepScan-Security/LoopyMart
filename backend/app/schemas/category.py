"""Category schemas for API request/response validation."""

from pydantic import BaseModel


class CategoryBase(BaseModel):
    """Base category schema with common fields."""
    name: str
    slug: str


class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""
    description: str | None = None
    image_url: str | None = None


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    image_url: str | None = None


class CategoryResponse(CategoryBase):
    """Schema for category response (MongoDB)."""
    id: str  # MongoDB ObjectId as string
    description: str | None = None
    image_url: str | None = None

    class Config:
        from_attributes = True
