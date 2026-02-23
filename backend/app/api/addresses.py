"""
Saved addresses API routes.

Addresses are stored in MongoDB (user_addresses collection).
Each user can have multiple addresses; one can be marked as default.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.db.addresses_mongo import (
    address_create,
    address_delete,
    address_get,
    address_list,
    address_set_default,
    address_update,
)
from app.models.user import User
from app.schemas.address import AddressCreate, AddressResponse, AddressUpdate

router = APIRouter(prefix="/addresses", tags=["addresses"])


def _to_response(doc: dict) -> AddressResponse:
    return AddressResponse(**doc)


@router.get("", response_model=list[AddressResponse])
async def list_addresses(
    current_user: User = Depends(get_current_user),
) -> list[AddressResponse]:
    """List all saved addresses for the current user (default first)."""
    docs = await address_list(current_user.id)
    return [_to_response(d) for d in docs]


@router.post("", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_address(
    data: AddressCreate,
    current_user: User = Depends(get_current_user),
) -> AddressResponse:
    """Create a new saved address."""
    doc = await address_create(current_user.id, data.model_dump())
    return _to_response(doc)


@router.patch("/{address_id}", response_model=AddressResponse)
async def update_address(
    address_id: str,
    data: AddressUpdate,
    current_user: User = Depends(get_current_user),
) -> AddressResponse:
    """Update fields on a saved address.  Pass `is_default: true` to also
    make this the default (clearing the flag from others)."""
    doc = await address_update(
        address_id, current_user.id, data.model_dump(exclude_unset=True)
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")
    return _to_response(doc)


@router.post("/{address_id}/default", response_model=AddressResponse)
async def set_default_address(
    address_id: str,
    current_user: User = Depends(get_current_user),
) -> AddressResponse:
    """Make this address the default, clearing the flag on all others."""
    doc = await address_set_default(address_id, current_user.id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")
    return _to_response(doc)


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(
    address_id: str,
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a saved address.  If it was the default, the most recent
    remaining address is promoted to default automatically."""
    deleted = await address_delete(address_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")
