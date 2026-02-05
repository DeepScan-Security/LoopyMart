"""
MongoDB operations for payments collection.
Payments are stored in MongoDB with the following schema:
{
    "_id": ObjectId,
    "order_id": str,
    "user_id": int,
    "amount": float,
    "payment_method": str,
    "status": str ("SUCCESS", "FAILED"),
    "payment_id": str,
    "created_at": datetime,
    "updated_at": datetime
}
"""

from datetime import datetime, timezone
import secrets

from bson import ObjectId
from bson.errors import InvalidId

from app.db.mongo import get_mongo_db


def _doc_to_payment(doc: dict) -> dict | None:
    """Convert MongoDB document to payment dict with string id."""
    if not doc:
        return None
    out = dict(doc)
    out["id"] = str(out["_id"])
    del out["_id"]
    return out


async def payment_create(
    order_id: str,
    user_id: int,
    amount: float,
    payment_method: str,
    status: str = "SUCCESS",
) -> dict:
    """Create a new payment record."""
    db = get_mongo_db()
    now = datetime.now(timezone.utc)
    
    # Generate dummy payment ID
    payment_id = f"PAY_{secrets.token_hex(8).upper()}"
    
    doc = {
        "order_id": order_id,
        "user_id": user_id,
        "amount": amount,
        "payment_method": payment_method,
        "status": status,
        "payment_id": payment_id,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.payments.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _doc_to_payment(doc)


async def payment_get(payment_id: str) -> dict | None:
    """Get a payment by ID."""
    try:
        oid = ObjectId(payment_id)
    except InvalidId:
        return None
    db = get_mongo_db()
    doc = await db.payments.find_one({"_id": oid})
    return _doc_to_payment(doc) if doc else None


async def payment_get_by_order(order_id: str) -> dict | None:
    """Get payment by order ID."""
    db = get_mongo_db()
    doc = await db.payments.find_one({"order_id": order_id})
    return _doc_to_payment(doc) if doc else None


async def payment_list_by_user(user_id: int, skip: int = 0, limit: int = 100) -> list[dict]:
    """List all payments for a user, newest first."""
    db = get_mongo_db()
    cursor = (
        db.payments.find({"user_id": user_id})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    return [_doc_to_payment(d) for d in docs]
