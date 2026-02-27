"""Seller application schemas for API request/response validation."""

from pydantic import BaseModel


class SellerApplicationCreate(BaseModel):
    """Schema for creating a seller application."""

    store_name: str
    store_description: str
    phone: str
    email: str
    address: str
    business_type: str  # "Individual", "Company", "Partnership", "LLP"
    gst_number: str | None = None
    pan_number: str
    bank_account_number: str
    bank_ifsc: str
    bank_account_name: str


class SellerApplicationResponse(BaseModel):
    """Schema for seller application response."""

    id: str
    user_id: int
    store_name: str
    store_description: str
    phone: str
    email: str
    address: str
    business_type: str
    gst_number: str | None = None
    pan_number: str
    bank_account_number: str
    bank_ifsc: str
    bank_account_name: str
    status: str  # "PENDING", "APPROVED", "REJECTED"
    remarks: str | None = None
    created_at: str
    updated_at: str


class SellerApplicationStatusUpdate(BaseModel):
    """Schema for updating seller application status (admin only)."""

    status: str  # "APPROVED" or "REJECTED"
    remarks: str | None = None
