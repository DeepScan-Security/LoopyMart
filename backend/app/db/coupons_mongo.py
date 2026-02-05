"""
MongoDB operations for coupons collection.
Coupons are stored in MongoDB with the following schema:
{
    "_id": ObjectId,
    "code": str,
    "discount": float,
    "description": str,
    "is_active": bool,
    "created_at": datetime
}

Coupon usage tracking:
{
    "_id": ObjectId,
    "user_id": int,
    "coupon_code": str,
    "used_at": datetime
}
"""

from datetime import datetime, timezone

from bson import ObjectId

from app.db.mongo import get_mongo_db


def _doc_to_coupon(doc: dict) -> dict | None:
    """Convert MongoDB document to coupon dict with string id."""
    if not doc:
        return None
    out = dict(doc)
    out["id"] = str(out["_id"])
    del out["_id"]
    return out


async def coupon_get_by_code(code: str) -> dict | None:
    """Get a coupon by code."""
    db = get_mongo_db()
    doc = await db.coupons.find_one({"code": code, "is_active": True})
    return _doc_to_coupon(doc) if doc else None


async def coupon_list_all() -> list[dict]:
    """List all active coupons."""
    db = get_mongo_db()
    cursor = db.coupons.find({"is_active": True})
    docs = await cursor.to_list(length=100)
    return [_doc_to_coupon(d) for d in docs]


async def coupon_check_usage(user_id: int, coupon_code: str) -> bool:
    """Check if user has already used this coupon."""
    db = get_mongo_db()
    doc = await db.coupon_usage.find_one({"user_id": user_id, "coupon_code": coupon_code})
    return doc is not None


async def coupon_mark_used(user_id: int, coupon_code: str) -> dict:
    """Mark coupon as used by user."""
    db = get_mongo_db()
    doc = {
        "user_id": user_id,
        "coupon_code": coupon_code,
        "used_at": datetime.now(timezone.utc),
    }
    result = await db.coupon_usage.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def coupon_create(code: str, discount: float, description: str) -> dict:
    """Create a new coupon."""
    db = get_mongo_db()
    doc = {
        "code": code,
        "discount": discount,
        "description": description,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.coupons.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _doc_to_coupon(doc)


async def coupon_seed_default():
    """Seed default 4 coupons if they don't exist."""
    db = get_mongo_db()
    
    default_coupons = [
        {"code": "WELCOME100", "discount": 100.0, "description": "Welcome bonus for new users"},
        {"code": "SAVE100", "discount": 100.0, "description": "Save ₹100 on your order"},
        {"code": "FIRSTBUY100", "discount": 100.0, "description": "First purchase discount"},
        {"code": "NEWUSER100", "discount": 100.0, "description": "New user special offer"},
    ]
    
    for coupon in default_coupons:
        existing = await db.coupons.find_one({"code": coupon["code"]})
        if not existing:
            await db.coupons.insert_one({
                **coupon,
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
            })
