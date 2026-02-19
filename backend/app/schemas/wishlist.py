"""Wishlist schemas for API request/response validation."""

from datetime import datetime

from pydantic import BaseModel


class WishlistCreate(BaseModel):
    """Schema for creating a new wishlist."""
    name: str


class WishlistRename(BaseModel):
    """Schema for renaming a wishlist."""
    name: str


class WishlistItemAdd(BaseModel):
    """Schema for adding a product to a wishlist."""
    product_id: str


class WishlistItemResponse(BaseModel):
    """Schema for a product entry inside a wishlist."""
    product_id: str
    product_name: str | None = None
    product_price: float | None = None
    product_image_url: str | None = None
    added_at: datetime | None = None


class WishlistResponse(BaseModel):
    """Schema for a wishlist response."""
    id: str
    name: str
    item_count: int = 0
    items: list[WishlistItemResponse] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class SharePreviewRequest(BaseModel):
    """Schema for the share-preview SSTI endpoint.

    The `share_template` field is rendered server-side with Jinja2.
    This is intentionally vulnerable for the CTF challenge.
    """
    share_template: str
