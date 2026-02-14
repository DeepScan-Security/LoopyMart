"""
Product Rating API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.db.ratings_mongo import (
    rating_check_user_purchased,
    rating_create,
    rating_get_by_user_product,
    rating_get_product_stats,
    rating_list_by_product,
    rating_update,
)
from app.models.user import User
from app.schemas.rating import ProductRatingStats, RatingCreate, RatingResponse

router = APIRouter(prefix="/ratings", tags=["ratings"])


@router.post("", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
async def create_rating(
    data: RatingCreate,
    current_user: User = Depends(get_current_user),
) -> RatingResponse:
    """Create or update a product rating."""
    # Check if user has purchased the product
    has_purchased = await rating_check_user_purchased(current_user.id, data.product_id)
    if not has_purchased:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can only rate products you have purchased.",
        )
    
    # Check if rating already exists
    existing_rating = await rating_get_by_user_product(current_user.id, data.product_id)
    
    if existing_rating:
        # Update existing rating
        rating = await rating_update(
            user_id=current_user.id,
            product_id=data.product_id,
            rating=data.rating,
            review=data.review,
        )
    else:
        # Create new rating
        rating = await rating_create(
            user_id=current_user.id,
            product_id=data.product_id,
            rating=data.rating,
            review=data.review,
        )
    
    if not rating:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create rating.",
        )
    
    return RatingResponse(
        id=rating["id"],
        user_id=rating["user_id"],
        product_id=rating["product_id"],
        rating=rating["rating"],
        review=rating.get("review"),
        created_at=rating["created_at"].isoformat(),
    )


@router.get("/product/{product_id}/stats", response_model=ProductRatingStats)
async def get_product_rating_stats(
    product_id: str,
) -> ProductRatingStats:
    """Get rating statistics for a product."""
    stats = await rating_get_product_stats(product_id)
    
    return ProductRatingStats(
        product_id=stats["product_id"],
        average_rating=stats["average_rating"],
        total_ratings=stats["total_ratings"],
    )


@router.get("/product/{product_id}", response_model=list[RatingResponse])
async def get_product_ratings(
    product_id: str,
) -> list[RatingResponse]:
    """Get all ratings for a product."""
    ratings = await rating_list_by_product(product_id)
    
    return [
        RatingResponse(
            id=rating["id"],
            user_id=rating["user_id"],
            product_id=rating["product_id"],
            rating=rating["rating"],
            review=rating.get("review"),
            created_at=rating["created_at"].isoformat(),
        )
        for rating in ratings
    ]


@router.get("/my-rating/{product_id}", response_model=RatingResponse | None)
async def get_my_rating(
    product_id: str,
    current_user: User = Depends(get_current_user),
) -> RatingResponse | None:
    """Get current user's rating for a product."""
    rating = await rating_get_by_user_product(current_user.id, product_id)
    
    if not rating:
        return None
    
    return RatingResponse(
        id=rating["id"],
        user_id=rating["user_id"],
        product_id=rating["product_id"],
        rating=rating["rating"],
        review=rating.get("review"),
        created_at=rating["created_at"].isoformat(),
    )
