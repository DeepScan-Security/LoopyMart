"""
MongoDB operations for products collection.
Products are stored in MongoDB with the following schema:
{
    "_id": ObjectId,
    "name": str,
    "description": str | None,
    "price": float,
    "image_url": str | None,
    "stock": int,
    "category_id": str (MongoDB ObjectId as string),
    "created_at": datetime,
    "updated_at": datetime
}
"""

import re
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument

from app.db.mongo import get_mongo_db


def _doc_to_product(doc: dict) -> dict | None:
    """Convert MongoDB document to product dict with string id."""
    if not doc:
        return None
    out = dict(doc)
    out["id"] = str(out["_id"])
    del out["_id"]
    return out


async def product_get(product_id: str) -> dict | None:
    """Get a product by its ID."""
    try:
        oid = ObjectId(product_id)
    except InvalidId:
        return None
    db = get_mongo_db()
    doc = await db.products.find_one({"_id": oid})
    return _doc_to_product(doc) if doc else None


async def product_get_by_name(name: str) -> dict | None:
    """Get a product by its name (case-insensitive exact match)."""
    db = get_mongo_db()
    doc = await db.products.find_one({"name": {"$regex": f"^{re.escape(name)}$", "$options": "i"}})
    return _doc_to_product(doc) if doc else None


async def product_list(
    category_id: str | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[dict]:
    """List products with optional category filter and search (name)."""
    db = get_mongo_db()
    filt = {}
    if category_id is not None:
        filt["category_id"] = category_id
    search_term = (search or "").strip()
    if search_term:
        # Search only by product name
        regex_pattern = re.escape(search_term).replace("\\ ", ".*")
        filt["name"] = {"$regex": regex_pattern, "$options": "i"}
    cursor = db.products.find(filt).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [_doc_to_product(d) for d in docs]


async def product_create(
    name: str,
    description: str | None,
    price: float,
    image_url: str | None,
    stock: int,
    category_id: str,
) -> dict:
    """Create a new product."""
    db = get_mongo_db()
    now = datetime.now(timezone.utc)
    doc = {
        "name": name,
        "description": description,
        "price": price,
        "image_url": image_url,
        "stock": stock,
        "category_id": category_id,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.products.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _doc_to_product(doc)


async def product_update(
    product_id: str,
    *,
    name: str | None = None,
    description: str | None = None,
    price: float | None = None,
    image_url: str | None = None,
    stock: int | None = None,
    category_id: str | None = None,
) -> dict | None:
    """Update a product."""
    try:
        oid = ObjectId(product_id)
    except InvalidId:
        return None
    db = get_mongo_db()
    updates = {"updated_at": datetime.now(timezone.utc)}
    if name is not None:
        updates["name"] = name
    if description is not None:
        updates["description"] = description
    if price is not None:
        updates["price"] = price
    if image_url is not None:
        updates["image_url"] = image_url
    if stock is not None:
        updates["stock"] = stock
    if category_id is not None:
        updates["category_id"] = category_id

    doc = await db.products.find_one_and_update(
        {"_id": oid},
        {"$set": updates},
        return_document=ReturnDocument.AFTER,
    )
    return _doc_to_product(doc) if doc else None


async def product_delete(product_id: str) -> bool:
    """Delete a product."""
    try:
        oid = ObjectId(product_id)
    except InvalidId:
        return False
    db = get_mongo_db()
    result = await db.products.delete_one({"_id": oid})
    return result.deleted_count > 0


async def product_decrement_stock(product_id: str, quantity: int) -> bool:
    """Atomically decrement product stock."""
    try:
        oid = ObjectId(product_id)
    except InvalidId:
        return False
    db = get_mongo_db()
    result = await db.products.update_one(
        {"_id": oid, "stock": {"$gte": quantity}},
        {
            "$inc": {"stock": -quantity},
            "$set": {"updated_at": datetime.now(timezone.utc)},
        },
    )
    return result.modified_count > 0
