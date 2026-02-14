"""
MongoDB operations for cart collection.
Cart items are stored in MongoDB with the following schema:
{
    "_id": ObjectId,
    "user_id": int (references SQL user),
    "product_id": str (MongoDB ObjectId as string),
    "quantity": int,
    "added_at": datetime,
    "updated_at": datetime
}
Index on (user_id, product_id) for uniqueness.
"""

from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument

from app.db.mongo import get_mongo_db


def _doc_to_cart_item(doc: dict) -> dict | None:
    """Convert MongoDB document to cart item dict with string id."""
    if not doc:
        return None
    out = dict(doc)
    out["id"] = str(out["_id"])
    del out["_id"]
    return out


async def cart_get_by_user(user_id: int) -> list[dict]:
    """Get all cart items for a user."""
    db = get_mongo_db()
    cursor = db.cart.find({"user_id": user_id}).sort("added_at", -1)
    docs = await cursor.to_list(length=1000)
    return [_doc_to_cart_item(d) for d in docs]


async def cart_get_item(user_id: int, product_id: str) -> dict | None:
    """Get a specific cart item for a user and product."""
    db = get_mongo_db()
    doc = await db.cart.find_one({"user_id": user_id, "product_id": product_id})
    return _doc_to_cart_item(doc) if doc else None


async def cart_get_item_by_id(item_id: str, user_id: int) -> dict | None:
    """Get a cart item by its ID, ensuring it belongs to the user."""
    try:
        oid = ObjectId(item_id)
    except InvalidId:
        return None
    db = get_mongo_db()
    doc = await db.cart.find_one({"_id": oid, "user_id": user_id})
    return _doc_to_cart_item(doc) if doc else None


async def cart_add_item(user_id: int, product_id: str, quantity: int) -> dict:
    """Add an item to cart or update quantity if exists."""
    db = get_mongo_db()
    now = datetime.now(timezone.utc)

    # Try to update existing item
    existing = await db.cart.find_one_and_update(
        {"user_id": user_id, "product_id": product_id},
        {
            "$inc": {"quantity": quantity},
            "$set": {"updated_at": now},
        },
        return_document=ReturnDocument.AFTER,
    )

    if existing:
        return _doc_to_cart_item(existing)

    # Create new cart item
    doc = {
        "user_id": user_id,
        "product_id": product_id,
        "quantity": quantity,
        "added_at": now,
        "updated_at": now,
    }
    result = await db.cart.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _doc_to_cart_item(doc)


async def cart_update_item(item_id: str, user_id: int, quantity: int) -> dict | None:
    """Update cart item quantity."""
    try:
        oid = ObjectId(item_id)
    except InvalidId:
        return None
    db = get_mongo_db()
    doc = await db.cart.find_one_and_update(
        {"_id": oid, "user_id": user_id},
        {
            "$set": {
                "quantity": quantity,
                "updated_at": datetime.now(timezone.utc),
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    return _doc_to_cart_item(doc) if doc else None


async def cart_set_quantity(item_id: str, user_id: int, quantity: int) -> dict | None:
    """Set cart item quantity to a specific value."""
    try:
        oid = ObjectId(item_id)
    except InvalidId:
        return None
    db = get_mongo_db()
    doc = await db.cart.find_one_and_update(
        {"_id": oid, "user_id": user_id},
        {
            "$set": {
                "quantity": quantity,
                "updated_at": datetime.now(timezone.utc),
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    return _doc_to_cart_item(doc) if doc else None


async def cart_remove_item(item_id: str, user_id: int) -> bool:
    """Remove a cart item."""
    try:
        oid = ObjectId(item_id)
    except InvalidId:
        return False
    db = get_mongo_db()
    result = await db.cart.delete_one({"_id": oid, "user_id": user_id})
    return result.deleted_count > 0


async def cart_clear(user_id: int) -> int:
    """Clear all cart items for a user. Returns number of items removed."""
    db = get_mongo_db()
    result = await db.cart.delete_many({"user_id": user_id})
    return result.deleted_count
