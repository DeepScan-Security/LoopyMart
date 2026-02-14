"""KYC schemas for API request/response validation."""

from pydantic import BaseModel


class KYCCreate(BaseModel):
    """Schema for creating KYC record."""
    document_type: str  # "AADHAR" or "PAN"
    document_number: str


class KYCResponse(BaseModel):
    """Schema for KYC response."""
    id: str
    user_id: int
    document_type: str
    document_number: str
    document_image_url: str | None = None
    status: str  # "PENDING", "VERIFIED", "REJECTED"
    created_at: str
    updated_at: str


class KYCStatusUpdate(BaseModel):
    """Schema for updating KYC status (admin only)."""
    status: str  # "VERIFIED" or "REJECTED"
    remarks: str | None = None
