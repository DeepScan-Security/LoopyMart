"""
MongoDB operations for ratings collection.
Ratings are stored in MongoDB with the following schema:
{
    "_id": ObjectId,
    "user_id": int,
    "product_id": str,
    "rating": int (1-5),
    "review": str | None,
    "created_at": datetime,
    "updated_at": datetime
}
"""

from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument

from app.db.mongo import get_mongo_db


def _doc_to_rating(doc: dict) -> dict | None:
    """Convert MongoDB document to rating dict with string id."""
    if not doc:
        return None
    out = dict(doc)
    out["id"] = str(out["_id"])
    del out["_id"]
    return out


async def rating_get_by_user_product(user_id: int, product_id: str) -> dict | None:
    """Get rating by user and product."""
    db = get_mongo_db()
    doc = await db.ratings.find_one({"user_id": user_id, "product_id": product_id})
    return _doc_to_rating(doc) if doc else None


async def rating_create(
    user_id: int,
    product_id: str,
    rating: int,
    review: str | None = None,
) -> dict:
    """Create a new rating."""
    db = get_mongo_db()
    now = datetime.now(timezone.utc)
    doc = {
        "user_id": user_id,
        "product_id": product_id,
        "rating": rating,
        "review": review,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.ratings.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _doc_to_rating(doc)


async def rating_update(
    user_id: int,
    product_id: str,
    rating: int,
    review: str | None = None,
) -> dict | None:
    """Update existing rating."""
    db = get_mongo_db()
    doc = await db.ratings.find_one_and_update(
        {"user_id": user_id, "product_id": product_id},
        {"$set": {
            "rating": rating,
            "review": review,
            "updated_at": datetime.now(timezone.utc),
        }},
        return_document=ReturnDocument.AFTER,
    )
    return _doc_to_rating(doc) if doc else None


async def rating_get_product_stats(product_id: str) -> dict:
    """Get rating statistics for a product."""
    db = get_mongo_db()
    
    # Calculate average rating and count
    pipeline = [
        {"$match": {"product_id": product_id}},
        {"$group": {
            "_id": None,
            "average_rating": {"$avg": "$rating"},
            "total_ratings": {"$sum": 1},
        }}
    ]
    
    result = await db.ratings.aggregate(pipeline).to_list(length=1)
    
    if result:
        return {
            "product_id": product_id,
            "average_rating": round(result[0]["average_rating"], 2),
            "total_ratings": result[0]["total_ratings"],
        }
    
    return {
        "product_id": product_id,
        "average_rating": 0.0,
        "total_ratings": 0,
    }


async def rating_list_by_product(product_id: str, skip: int = 0, limit: int = 50) -> list[dict]:
    """List all ratings for a product."""
    db = get_mongo_db()
    cursor = (
        db.ratings.find({"product_id": product_id})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    return [_doc_to_rating(d) for d in docs]


async def rating_check_user_purchased(user_id: int, product_id: str) -> bool:
    """Check if user has purchased the product."""
    db = get_mongo_db()
    
    # Check if user has any completed order with this product
    order = await db.orders.find_one({
        "user_id": user_id,
        "status": {"$in": ["paid", "shipped", "delivered"]},
        "items.product_id": product_id,
    })
    
    return order is not None
