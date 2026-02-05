"""
MongoDB operations for KYC collection.
KYC records are stored in MongoDB with the following schema:
{
    "_id": ObjectId,
    "user_id": int,
    "document_type": str ("AADHAR", "PAN"),
    "document_number": str,
    "document_image_url": str | None,
    "status": str ("PENDING", "VERIFIED", "REJECTED"),
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


def _doc_to_kyc(doc: dict) -> dict | None:
    """Convert MongoDB document to KYC dict with string id."""
    if not doc:
        return None
    out = dict(doc)
    out["id"] = str(out["_id"])
    del out["_id"]
    return out


async def kyc_get_by_user(user_id: int) -> dict | None:
    """Get KYC record by user ID."""
    db = get_mongo_db()
    doc = await db.kyc.find_one({"user_id": user_id})
    return _doc_to_kyc(doc) if doc else None


async def kyc_get(kyc_id: str) -> dict | None:
    """Get KYC record by ID."""
    try:
        oid = ObjectId(kyc_id)
    except InvalidId:
        return None
    db = get_mongo_db()
    doc = await db.kyc.find_one({"_id": oid})
    return _doc_to_kyc(doc) if doc else None


async def kyc_create(
    user_id: int,
    document_type: str,
    document_number: str,
    document_image_url: str | None = None,
) -> dict:
    """Create a new KYC record."""
    db = get_mongo_db()
    now = datetime.now(timezone.utc)
    doc = {
        "user_id": user_id,
        "document_type": document_type,
        "document_number": document_number,
        "document_image_url": document_image_url,
        "status": "PENDING",
        "remarks": None,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.kyc.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _doc_to_kyc(doc)


async def kyc_update(
    kyc_id: str,
    status: str | None = None,
    remarks: str | None = None,
    document_image_url: str | None = None,
) -> dict | None:
    """Update KYC record."""
    try:
        oid = ObjectId(kyc_id)
    except InvalidId:
        return None
    
    db = get_mongo_db()
    updates = {"updated_at": datetime.now(timezone.utc)}
    
    if status is not None:
        updates["status"] = status
    if remarks is not None:
        updates["remarks"] = remarks
    if document_image_url is not None:
        updates["document_image_url"] = document_image_url
    
    doc = await db.kyc.find_one_and_update(
        {"_id": oid},
        {"$set": updates},
        return_document=ReturnDocument.AFTER,
    )
    return _doc_to_kyc(doc) if doc else None


async def kyc_list_all(skip: int = 0, limit: int = 100) -> list[dict]:
    """List all KYC records (admin)."""
    db = get_mongo_db()
    cursor = (
        db.kyc.find()
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    return [_doc_to_kyc(d) for d in docs]
