"""Rating schemas for API request/response validation."""

from pydantic import BaseModel, Field


class RatingCreate(BaseModel):
    """Schema for creating a product rating."""
    product_id: str
    rating: int = Field(..., ge=1, le=5)
    review: str | None = None


class RatingResponse(BaseModel):
    """Schema for rating response."""
    id: str
    user_id: int
    product_id: str
    rating: int
    review: str | None = None
    created_at: str


class ProductRatingStats(BaseModel):
    """Schema for product rating statistics."""
    product_id: str
    average_rating: float
    total_ratings: int
