"""Pydantic schemas for saved addresses."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_validator


class AddressCreate(BaseModel):
    full_name: str
    phone: str
    pincode: str
    address_line1: str
    address_line2: str = ""
    landmark: str = ""
    city: str
    state: str
    country: str = "India"
    address_type: str = "Home"
    is_default: bool = False

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        digits = v.strip()
        if not digits.isdigit() or len(digits) != 10:
            raise ValueError("Phone must be a 10-digit number")
        return digits

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: str) -> str:
        digits = v.strip()
        if not digits.isdigit() or len(digits) != 6:
            raise ValueError("PIN code must be a 6-digit number")
        return digits

    @field_validator("full_name", "address_line1", "city", "state")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("This field cannot be empty")
        return v.strip()


class AddressUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    pincode: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    landmark: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    address_type: str | None = None
    is_default: bool | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        digits = v.strip()
        if not digits.isdigit() or len(digits) != 10:
            raise ValueError("Phone must be a 10-digit number")
        return digits

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: str | None) -> str | None:
        if v is None:
            return v
        digits = v.strip()
        if not digits.isdigit() or len(digits) != 6:
            raise ValueError("PIN code must be a 6-digit number")
        return digits


class AddressResponse(BaseModel):
    id: str
    user_id: int
    full_name: str
    phone: str
    pincode: str
    address_line1: str
    address_line2: str = ""
    landmark: str = ""
    city: str
    state: str
    country: str = "India"
    address_type: str = "Home"
    is_default: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
