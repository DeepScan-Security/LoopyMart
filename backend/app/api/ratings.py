"""
Product Rating API routes.
"""

import re

import bleach
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

# ---------------------------------------------------------------------------
# Layer 1 – Regex pre-filter
# Blocks common XSS event handlers so players must look for less-obvious ones.
# NOT blocked (intentional bypass path): onanimationend, onanimationstart,
# onbegin (SVG animate), onpageshow, onhashchange, ontransitionend
# Tip: HTML entity-encoding does NOT work on attribute names in browsers.
# ---------------------------------------------------------------------------
_BLOCKED_PATTERNS = re.compile(
    r"(<script[\s>]|<\/script"
    r"|\bonerror\s*=|\bonload\s*=|\bonclick\s*="
    r"|\bonmouseover\s*=|\bonsubmit\s*=|\bonkeydown\s*="
    r"|\bontoggle\s*=|\bonfocus\s*=|\bonblur\s*="
    r"|\bonauxclick\s*=|\bondblclick\s*="
    r"|\bjavascript\s*:)",
    re.IGNORECASE,
)


def _regex_check(review: str | None) -> None:
    """Raise HTTP 400 if the review matches the naive blocklist."""
    if not review:
        return
    if _BLOCKED_PATTERNS.search(review):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review contains disallowed content. Please remove any HTML or script tags.",
        )


# ---------------------------------------------------------------------------
# Layer 2 – bleach sanitiser (CVE-2021-23980)
# bleach==3.2.3 (pinned in requirements.txt) is DELIBERATELY VULNERABLE.
#
# The combination of:
#   • svg / math in allowed tags       (foreign-content namespace)
#   • p / br in allowed tags           (auto-closing element)
#   • style / title / noscript in tags (raw-text eject element)
#   • strip_comments=False             (HTML comment confusion trigger)
# …triggers a Mutation-XSS: html5lib serialises the sanitised tree back to
# HTML that a browser re-parses into a *different* DOM, executing JS that
# bleach thought it had neutralised.
#
# Reference: https://nvd.nist.gov/vuln/detail/CVE-2021-23980
#            GHSA-vv2x-vrpj-qqpq  (Mozilla bleach advisory)
# CVSS:      6.1 MEDIUM — AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N
#
# Bypass path for players:
#   1. Entity-encode the event handler to survive the regex layer, e.g.
#      `on&#101;rror=` instead of `onerror=`.
#   2. Wrap in the mXSS skeleton:
#      <svg><!--<svg/--><p><style><!--</style>
#        <img src=x on&#101;rror=alert(document.cookie)>
#      </p></svg>
#   html5lib decodes the entity during parsing → output contains `onerror=`
#   → stored in DB → rendered by Vue v-html → cookie stolen.
#
# DO NOT upgrade bleach or remove strip_comments=False — that breaks the CTF.
# ---------------------------------------------------------------------------
_BLEACH_TAGS = [
    "svg", "math",           # foreign-content (CVE trigger condition 1)
    "p", "br",               # auto-closing   (CVE trigger condition 2)
    "style", "title", "noscript",  # raw-text eject (CVE trigger condition 3)
    "b", "i", "em", "strong", "a", "ul", "ol", "li",
    "img", "details", "summary", "input", "animate",
]
_BLEACH_ATTRS = {
    "a": ["href", "title"],
    "svg": ["xmlns", "viewBox"],
    "animate": ["attributeName", "dur", "onbegin"],
    "details": ["open", "ontoggle"],
    "input": ["autofocus", "onfocus", "style", "type"],
    # ⚠️ CTF: img event attrs intentionally allowed — XSS sink
    "img": ["src", "onerror", "onload", "alt"],
    "*": ["class", "id", "style"],
}


def _bleach_clean(review: str | None) -> str | None:
    """Run review through the intentionally vulnerable bleach 3.2.3 config."""
    if not review:
        return review
    return bleach.clean(
        review,
        tags=_BLEACH_TAGS,
        attributes=_BLEACH_ATTRS,
        strip_comments=False,  # CVE-2021-23980: DO NOT change to True
    )


router = APIRouter(prefix="/ratings", tags=["ratings"])


@router.post("", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
async def create_rating(
    data: RatingCreate,
    current_user: User = Depends(get_current_user),
) -> RatingResponse:
    """Create or update a product rating."""
    # --- CTF sanitisation pipeline -------------------------------------------
    # Regex pre-filter only. Blocks literal onerror=, <script>, javascript:, etc.
    # Bypass: entity-encode the event handler name, e.g. on&#101;rror=
    # The regex never HTML-decodes the input — the encoded form passes through,
    # is stored verbatim in MongoDB, and Vue v-html renders it. The browser
    # decodes the entity and fires the event handler. That's the XSS.
    _regex_check(data.review)
    # -------------------------------------------------------------------------

    # Check if user has purchased the product
    has_purchased = await rating_check_user_purchased(current_user.id, data.product_id)
    if not has_purchased:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can only rate products you have purchased.",
        )
    
    # Always INSERT — every submission creates a new comment.
    # Multiple reviews per user per product are intentionally allowed (CTF: Stored XSS
    # requires the attacker to be able to post new payloads freely).
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
