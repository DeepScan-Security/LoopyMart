"""
MongoDB operations for orders collection.
Orders are stored in MongoDB with the following schema:
{
    "_id": ObjectId,
    "user_id": int (references SQL user),
    "total": float,
    "status": str ("pending", "paid", "shipped", "delivered", "cancelled"),
    "shipping_address": dict | str,  # structured ShippingAddressSchema dict or legacy string
    "items": [
        {
            "product_id": str,
            "product_name": str,
            "quantity": int,
            "price_at_order": float,
            "product_image_url": str | None
        }
    ],
    "razorpay_order_id": str | None,
    "razorpay_payment_id": str | None,
    "created_at": datetime,
    "updated_at": datetime
}
"""

from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument

from app.db.mongo import get_mongo_db


def _doc_to_order(doc: dict) -> dict | None:
    """Convert MongoDB document to order dict with string id."""
    if not doc:
        return None
    out = dict(doc)
    out["id"] = str(out["_id"])
    del out["_id"]
    return out


async def order_get(order_id: str, user_id: int | None = None) -> dict | None:
    """Get an order by ID, optionally filtered by user_id."""
    try:
        oid = ObjectId(order_id)
    except InvalidId:
        return None
    db = get_mongo_db()
    query = {"_id": oid}
    if user_id is not None:
        query["user_id"] = user_id
    doc = await db.orders.find_one(query)
    return _doc_to_order(doc) if doc else None


async def order_list_by_user(user_id: int, skip: int = 0, limit: int = 100) -> list[dict]:
    """List all orders for a user, newest first."""
    db = get_mongo_db()
    cursor = (
        db.orders.find({"user_id": user_id})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    return [_doc_to_order(d) for d in docs]


async def order_list_all(skip: int = 0, limit: int = 100) -> list[dict]:
    """List all orders (admin), newest first."""
    db = get_mongo_db()
    cursor = (
        db.orders.find()
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    return [_doc_to_order(d) for d in docs]


async def order_create(
    user_id: int,
    total: float,
    shipping_address: dict | str,
    items: list[dict],
    status: str = "pending",
    razorpay_order_id: str | None = None,
) -> dict:
    """Create a new order."""
    db = get_mongo_db()
    now = datetime.now(timezone.utc)
    doc = {
        "user_id": user_id,
        "total": total,
        "status": status,
        "shipping_address": shipping_address,
        "items": items,
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": None,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.orders.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _doc_to_order(doc)


async def order_update_status(
    order_id: str,
    status: str,
    user_id: int | None = None,
    razorpay_payment_id: str | None = None,
) -> dict | None:
    """Update order status."""
    try:
        oid = ObjectId(order_id)
    except InvalidId:
        return None
    db = get_mongo_db()
    query = {"_id": oid}
    if user_id is not None:
        query["user_id"] = user_id

    updates = {
        "status": status,
        "updated_at": datetime.now(timezone.utc),
    }
    if razorpay_payment_id:
        updates["razorpay_payment_id"] = razorpay_payment_id

    doc = await db.orders.find_one_and_update(
        query,
        {"$set": updates},
        return_document=ReturnDocument.AFTER,
    )
    return _doc_to_order(doc) if doc else None


async def order_update(
    order_id: str,
    *,
    status: str | None = None,
    shipping_address: dict | str | None = None,
    razorpay_order_id: str | None = None,
    razorpay_payment_id: str | None = None,
) -> dict | None:
    """Update order fields."""
    try:
        oid = ObjectId(order_id)
    except InvalidId:
        return None
    db = get_mongo_db()
    updates = {"updated_at": datetime.now(timezone.utc)}

    if status is not None:
        updates["status"] = status
    if shipping_address is not None:
        updates["shipping_address"] = shipping_address
    if razorpay_order_id is not None:
        updates["razorpay_order_id"] = razorpay_order_id
    if razorpay_payment_id is not None:
        updates["razorpay_payment_id"] = razorpay_payment_id

    doc = await db.orders.find_one_and_update(
        {"_id": oid},
        {"$set": updates},
        return_document=ReturnDocument.AFTER,
    )
    return _doc_to_order(doc) if doc else None


async def order_count_by_user(user_id: int) -> int:
    """Count orders for a user."""
    db = get_mongo_db()
    return await db.orders.count_documents({"user_id": user_id})
