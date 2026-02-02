"""
MongoDB operations for categories collection.
Categories are stored in MongoDB with the following schema:
{
    "_id": ObjectId,
    "name": str,
    "slug": str (unique, indexed),
    "description": str | None,
    "image_url": str | None,
    "created_at": datetime,
    "updated_at": datetime
}
"""

from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument

from app.db.mongo import get_mongo_db


def _doc_to_category(doc: dict) -> dict | None:
    """Convert MongoDB document to category dict with string id."""
    if not doc:
        return None
    out = dict(doc)
    out["id"] = str(out["_id"])
    del out["_id"]
    return out


async def category_get(category_id: str) -> dict | None:
    """Get a category by its ID."""
    try:
        oid = ObjectId(category_id)
    except InvalidId:
        return None
    db = get_mongo_db()
    doc = await db.categories.find_one({"_id": oid})
    return _doc_to_category(doc) if doc else None


async def category_get_by_slug(slug: str) -> dict | None:
    """Get a category by its slug."""
    db = get_mongo_db()
    doc = await db.categories.find_one({"slug": slug})
    return _doc_to_category(doc) if doc else None


async def category_list() -> list[dict]:
    """List all categories ordered by name."""
    db = get_mongo_db()
    cursor = db.categories.find().sort("name", 1)
    docs = await cursor.to_list(length=1000)
    return [_doc_to_category(d) for d in docs]


async def category_create(
    name: str,
    slug: str,
    description: str | None = None,
    image_url: str | None = None,
) -> dict:
    """Create a new category."""
    db = get_mongo_db()
    now = datetime.now(timezone.utc)
    doc = {
        "name": name,
        "slug": slug,
        "description": description,
        "image_url": image_url,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.categories.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _doc_to_category(doc)


async def category_update(
    category_id: str,
    *,
    name: str | None = None,
    slug: str | None = None,
    description: str | None = None,
    image_url: str | None = None,
) -> dict | None:
    """Update a category."""
    try:
        oid = ObjectId(category_id)
    except InvalidId:
        return None
    db = get_mongo_db()
    updates = {"updated_at": datetime.now(timezone.utc)}
    if name is not None:
        updates["name"] = name
    if slug is not None:
        updates["slug"] = slug
    if description is not None:
        updates["description"] = description
    if image_url is not None:
        updates["image_url"] = image_url

    doc = await db.categories.find_one_and_update(
        {"_id": oid},
        {"$set": updates},
        return_document=ReturnDocument.AFTER,
    )
    return _doc_to_category(doc) if doc else None


async def category_delete(category_id: str) -> bool:
    """Delete a category."""
    try:
        oid = ObjectId(category_id)
    except InvalidId:
        return False
    db = get_mongo_db()
    result = await db.categories.delete_one({"_id": oid})
    return result.deleted_count > 0


async def category_exists(slug: str) -> bool:
    """Check if a category with the given slug exists."""
    db = get_mongo_db()
    doc = await db.categories.find_one({"slug": slug}, {"_id": 1})
    return doc is not None
