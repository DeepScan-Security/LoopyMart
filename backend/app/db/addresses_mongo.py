"""
MongoDB operations for user_addresses collection.

Schema per document:
{
    "_id": ObjectId,
    "user_id": int,            # references SQL user
    "full_name": str,
    "phone": str,
    "pincode": str,
    "address_line1": str,
    "address_line2": str,
    "landmark": str,
    "city": str,
    "state": str,
    "country": str,
    "address_type": str,       # "Home" | "Work" | "Other"
    "is_default": bool,
    "created_at": datetime,
    "updated_at": datetime,
}
"""
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument

from app.db.mongo import get_mongo_db

_ADDR_FIELDS = (
    "full_name", "phone", "pincode", "address_line1", "address_line2",
    "landmark", "city", "state", "country", "address_type",
)


def _doc_to_addr(doc: dict) -> dict | None:
    if not doc:
        return None
    out = dict(doc)
    out["id"] = str(out.pop("_id"))
    return out


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

async def address_list(user_id: int) -> list[dict]:
    """Return all addresses for a user, default first, then newest."""
    db = get_mongo_db()
    # Sort: default desc (True > False), then created_at desc
    cursor = db.user_addresses.find({"user_id": user_id}).sort(
        [("is_default", -1), ("created_at", -1)]
    )
    docs = await cursor.to_list(length=100)
    return [_doc_to_addr(d) for d in docs]


async def address_get(address_id: str, user_id: int) -> dict | None:
    """Get a single address owned by the user."""
    try:
        oid = ObjectId(address_id)
    except InvalidId:
        return None
    db = get_mongo_db()
    doc = await db.user_addresses.find_one({"_id": oid, "user_id": user_id})
    return _doc_to_addr(doc) if doc else None


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

async def address_create(user_id: int, data: dict) -> dict:
    """
    Create a new address.  If this is the user's first address it is
    automatically marked as default (regardless of the `is_default` flag
    supplied by the caller).  Otherwise, if the caller explicitly passes
    `is_default=True` the old default is cleared first.
    """
    db = get_mongo_db()
    now = datetime.now(timezone.utc)

    # Determine whether to set as default
    existing_count = await db.user_addresses.count_documents({"user_id": user_id})
    make_default = (existing_count == 0) or bool(data.get("is_default"))

    if make_default:
        # Clear any existing default for this user
        await db.user_addresses.update_many(
            {"user_id": user_id, "is_default": True},
            {"$set": {"is_default": False, "updated_at": now}},
        )

    doc = {
        "user_id": user_id,
        "is_default": make_default,
        "created_at": now,
        "updated_at": now,
    }
    for field in _ADDR_FIELDS:
        doc[field] = data.get(field, "")

    result = await db.user_addresses.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _doc_to_addr(doc)


async def address_update(address_id: str, user_id: int, patch: dict) -> dict | None:
    """Update allowed fields on an address.  If `is_default=True` in patch,
    the old default is cleared before setting this one."""
    try:
        oid = ObjectId(address_id)
    except InvalidId:
        return None
    db = get_mongo_db()
    now = datetime.now(timezone.utc)

    if patch.get("is_default"):
        await db.user_addresses.update_many(
            {"user_id": user_id, "is_default": True},
            {"$set": {"is_default": False, "updated_at": now}},
        )

    update_fields: dict = {"updated_at": now}
    for field in list(_ADDR_FIELDS) + ["is_default"]:
        if field in patch and patch[field] is not None:
            update_fields[field] = patch[field]

    doc = await db.user_addresses.find_one_and_update(
        {"_id": oid, "user_id": user_id},
        {"$set": update_fields},
        return_document=ReturnDocument.AFTER,
    )
    return _doc_to_addr(doc) if doc else None


async def address_set_default(address_id: str, user_id: int) -> dict | None:
    """Mark one address as the default, clearing the flag on all others."""
    try:
        oid = ObjectId(address_id)
    except InvalidId:
        return None
    db = get_mongo_db()
    now = datetime.now(timezone.utc)

    # Verify it belongs to the user
    existing = await db.user_addresses.find_one({"_id": oid, "user_id": user_id})
    if not existing:
        return None

    # Clear current default(s)
    await db.user_addresses.update_many(
        {"user_id": user_id, "is_default": True},
        {"$set": {"is_default": False, "updated_at": now}},
    )
    # Set the new default
    doc = await db.user_addresses.find_one_and_update(
        {"_id": oid, "user_id": user_id},
        {"$set": {"is_default": True, "updated_at": now}},
        return_document=ReturnDocument.AFTER,
    )
    return _doc_to_addr(doc) if doc else None


async def address_delete(address_id: str, user_id: int) -> bool:
    """Delete an address.  If it was the default, promote the most recent remaining
    address (if any) to be the new default."""
    try:
        oid = ObjectId(address_id)
    except InvalidId:
        return False
    db = get_mongo_db()

    doc = await db.user_addresses.find_one({"_id": oid, "user_id": user_id})
    if not doc:
        return False

    was_default = doc.get("is_default", False)
    result = await db.user_addresses.delete_one({"_id": oid, "user_id": user_id})
    if result.deleted_count == 0:
        return False

    # If we deleted the default, promote the most recent remaining address
    if was_default:
        now = datetime.now(timezone.utc)
        next_doc = await db.user_addresses.find_one(
            {"user_id": user_id},
            sort=[("created_at", -1)],
        )
        if next_doc:
            await db.user_addresses.update_one(
                {"_id": next_doc["_id"]},
                {"$set": {"is_default": True, "updated_at": now}},
            )

    return True
