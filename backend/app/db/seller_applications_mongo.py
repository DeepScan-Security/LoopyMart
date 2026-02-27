"""
MongoDB operations for seller_applications collection.
Seller applications are stored in MongoDB with the following schema:
{
    "_id": ObjectId,
    "user_id": int,
    "store_name": str,
    "store_description": str,
    "phone": str,
    "email": str,
    "address": str,
    "business_type": str,
    "gst_number": str | None,
    "pan_number": str,
    "bank_account_number": str,
    "bank_ifsc": str,
    "bank_account_name": str,
    "status": str ("PENDING", "APPROVED", "REJECTED"),
    "remarks": str | None,
    "created_at": datetime,
    "updated_at": datetime
}
"""

from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument

from app.db.mongo import get_mongo_db


def _doc_to_app(doc: dict) -> dict | None:
    """Convert MongoDB document to seller application dict with string id."""
    if not doc:
        return None
    out = dict(doc)
    out["id"] = str(out["_id"])
    del out["_id"]
    return out


async def seller_app_get_by_user(user_id: int) -> dict | None:
    """Get seller application by user ID."""
    db = get_mongo_db()
    doc = await db.seller_applications.find_one({"user_id": user_id})
    return _doc_to_app(doc) if doc else None


async def seller_app_get(app_id: str) -> dict | None:
    """Get seller application by ID."""
    try:
        oid = ObjectId(app_id)
    except InvalidId:
        return None
    db = get_mongo_db()
    doc = await db.seller_applications.find_one({"_id": oid})
    return _doc_to_app(doc) if doc else None


async def seller_app_create(
    user_id: int,
    store_name: str,
    store_description: str,
    phone: str,
    email: str,
    address: str,
    business_type: str,
    gst_number: str | None,
    pan_number: str,
    bank_account_number: str,
    bank_ifsc: str,
    bank_account_name: str,
) -> dict:
    """Create a new seller application."""
    db = get_mongo_db()
    now = datetime.now(timezone.utc)
    doc = {
        "user_id": user_id,
        "store_name": store_name,
        "store_description": store_description,
        "phone": phone,
        "email": email,
        "address": address,
        "business_type": business_type,
        "gst_number": gst_number,
        "pan_number": pan_number,
        "bank_account_number": bank_account_number,
        "bank_ifsc": bank_ifsc,
        "bank_account_name": bank_account_name,
        "status": "PENDING",
        "remarks": None,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.seller_applications.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _doc_to_app(doc)


async def seller_app_update_status(
    app_id: str,
    status: str,
    remarks: str | None = None,
) -> dict | None:
    """Update seller application status."""
    try:
        oid = ObjectId(app_id)
    except InvalidId:
        return None
    db = get_mongo_db()
    update_fields: dict = {
        "status": status,
        "updated_at": datetime.now(timezone.utc),
    }
    if remarks is not None:
        update_fields["remarks"] = remarks
    doc = await db.seller_applications.find_one_and_update(
        {"_id": oid},
        {"$set": update_fields},
        return_document=ReturnDocument.AFTER,
    )
    return _doc_to_app(doc) if doc else None


async def seller_app_list_all() -> list[dict]:
    """List all seller applications, newest first."""
    db = get_mongo_db()
    cursor = db.seller_applications.find().sort("created_at", -1)
    return [_doc_to_app(doc) for doc in await cursor.to_list(length=None)]
