"""
Seller application API routes.
Users submit applications to become sellers; admins approve/reject via /admin endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.db.seller_applications_mongo import (
    seller_app_create,
    seller_app_get_by_user,
)
from app.models.user import User
from app.schemas.seller import SellerApplicationCreate, SellerApplicationResponse

router = APIRouter(prefix="/seller", tags=["seller"])


def _to_response(app: dict) -> SellerApplicationResponse:
    """Convert Mongo dict to SellerApplicationResponse."""
    return SellerApplicationResponse(
        id=app["id"],
        user_id=app["user_id"],
        store_name=app["store_name"],
        store_description=app["store_description"],
        phone=app["phone"],
        email=app["email"],
        address=app["address"],
        business_type=app["business_type"],
        gst_number=app.get("gst_number"),
        pan_number=app["pan_number"],
        bank_account_number=app["bank_account_number"],
        bank_ifsc=app["bank_ifsc"],
        bank_account_name=app["bank_account_name"],
        status=app["status"],
        remarks=app.get("remarks"),
        created_at=app["created_at"].isoformat(),
        updated_at=app["updated_at"].isoformat(),
    )


@router.post("/apply", response_model=SellerApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply_seller(
    data: SellerApplicationCreate,
    current_user: User = Depends(get_current_user),
) -> SellerApplicationResponse:
    """Submit a seller application. Only one application allowed per user."""
    existing = await seller_app_get_by_user(current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a seller application. Check its status below.",
        )

    app = await seller_app_create(
        user_id=current_user.id,
        store_name=data.store_name,
        store_description=data.store_description,
        phone=data.phone,
        email=data.email,
        address=data.address,
        business_type=data.business_type,
        gst_number=data.gst_number,
        pan_number=data.pan_number,
        bank_account_number=data.bank_account_number,
        bank_ifsc=data.bank_ifsc,
        bank_account_name=data.bank_account_name,
    )
    return _to_response(app)


@router.get("/me", response_model=SellerApplicationResponse | None)
async def get_my_application(
    current_user: User = Depends(get_current_user),
) -> SellerApplicationResponse | None:
    """Get the current user's seller application."""
    app = await seller_app_get_by_user(current_user.id)
    if not app:
        return None
    return _to_response(app)
