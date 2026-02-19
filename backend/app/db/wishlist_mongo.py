"""
MongoDB operations for wishlists collection.

Schema:
{
    "_id": ObjectId,
    "user_id": int (references SQL user),
    "name": str,
    "created_at": datetime,
    "updated_at": datetime,
    "items": [
        {
            "product_id": str,
            "added_at": datetime
        }
    ]
}
"""

from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument

from app.db.mongo import get_mongo_db


def _doc_to_wishlist(doc: dict) -> dict | None:
    """Convert MongoDB document to wishlist dict with string id."""
    if not doc:
        return None
    out = dict(doc)
    out["id"] = str(out["_id"])
    del out["_id"]
    return out


async def wishlist_get_all_by_user(user_id: int) -> list[dict]:
    """Get all wishlists for a user."""
    db = get_mongo_db()
    cursor = db.wishlists.find({"user_id": user_id}).sort("created_at", -1)
    docs = await cursor.to_list(length=1000)
    return [_doc_to_wishlist(d) for d in docs]


async def wishlist_get_by_id(wishlist_id: str, user_id: int) -> dict | None:
    """Get a wishlist by ID, ensuring it belongs to the user."""
    try:
        oid = ObjectId(wishlist_id)
    except InvalidId:
        return None
    db = get_mongo_db()
    doc = await db.wishlists.find_one({"_id": oid, "user_id": user_id})
    return _doc_to_wishlist(doc) if doc else None


async def wishlist_create(user_id: int, name: str) -> dict:
    """Create a new wishlist for a user."""
    db = get_mongo_db()
    now = datetime.now(timezone.utc)
    doc = {
        "user_id": user_id,
        "name": name,
        "items": [],
        "created_at": now,
        "updated_at": now,
    }
    result = await db.wishlists.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _doc_to_wishlist(doc)


async def wishlist_rename(wishlist_id: str, user_id: int, name: str) -> dict | None:
    """Rename a wishlist."""
    try:
        oid = ObjectId(wishlist_id)
    except InvalidId:
        return None
    db = get_mongo_db()
    doc = await db.wishlists.find_one_and_update(
        {"_id": oid, "user_id": user_id},
        {"$set": {"name": name, "updated_at": datetime.now(timezone.utc)}},
        return_document=ReturnDocument.AFTER,
    )
    return _doc_to_wishlist(doc) if doc else None


async def wishlist_delete(wishlist_id: str, user_id: int) -> bool:
    """Delete a wishlist."""
    try:
        oid = ObjectId(wishlist_id)
    except InvalidId:
        return False
    db = get_mongo_db()
    result = await db.wishlists.delete_one({"_id": oid, "user_id": user_id})
    return result.deleted_count > 0


async def wishlist_add_item(wishlist_id: str, user_id: int, product_id: str) -> dict | None:
    """Add a product to a wishlist (no duplicates per wishlist)."""
    try:
        oid = ObjectId(wishlist_id)
    except InvalidId:
        return None
    db = get_mongo_db()
    now = datetime.now(timezone.utc)

    # Check if item already exists
    existing = await db.wishlists.find_one(
        {"_id": oid, "user_id": user_id, "items.product_id": product_id}
    )
    if existing:
        return _doc_to_wishlist(existing)

    doc = await db.wishlists.find_one_and_update(
        {"_id": oid, "user_id": user_id},
        {
            "$push": {"items": {"product_id": product_id, "added_at": now}},
            "$set": {"updated_at": now},
        },
        return_document=ReturnDocument.AFTER,
    )
    return _doc_to_wishlist(doc) if doc else None


async def wishlist_remove_item(wishlist_id: str, user_id: int, product_id: str) -> dict | None:
    """Remove a product from a wishlist."""
    try:
        oid = ObjectId(wishlist_id)
    except InvalidId:
        return None
    db = get_mongo_db()
    doc = await db.wishlists.find_one_and_update(
        {"_id": oid, "user_id": user_id},
        {
            "$pull": {"items": {"product_id": product_id}},
            "$set": {"updated_at": datetime.now(timezone.utc)},
        },
        return_document=ReturnDocument.AFTER,
    )
    return _doc_to_wishlist(doc) if doc else None


async def wishlist_product_in_user_wishlists(user_id: int, product_id: str) -> list[str]:
    """Return list of wishlist IDs (as strings) that contain the given product_id for a user."""
    db = get_mongo_db()
    cursor = db.wishlists.find(
        {"user_id": user_id, "items.product_id": product_id},
        {"_id": 1},
    )
    docs = await cursor.to_list(length=1000)
    return [str(d["_id"]) for d in docs]
