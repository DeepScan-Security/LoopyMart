"""
MongoDB operations for the support_tickets collection.

Schema:
{
    "_id": ObjectId,
    "ticket_uuid": str,       # UUIDv1 string — the public identifier
    "user_id": int,           # 0 = internal/system ticket
    "subject": str,
    "message": str,
    "is_internal": bool,      # True for the hidden CTF sandwich ticket
    "flag": str | None,       # Populated only for the internal ticket
    "created_at": datetime,
}

IDOR surface
------------
``ticket_get_by_uuid`` fetches by ``ticket_uuid`` **only** — no ``user_id``
ownership check is performed.  This is intentional; it is the CTF sink.

UUID Sandwich mechanic
----------------------
Every call to ``ticket_create`` for a regular user creates one additional
hidden internal ticket immediately afterwards.  Because ``uuid.uuid1()`` is
time-ordered, the internal ticket UUID always falls *between* the UUIDs of
the two consecutive user-created tickets, forming a "sandwich".
"""

from datetime import datetime, timezone
from uuid import uuid1

from app.db.mongo import get_mongo_db


def _doc_to_ticket(doc: dict) -> dict | None:
    if not doc:
        return None
    out = dict(doc)
    out.pop("_id", None)
    return out


async def ticket_create(
    user_id: int,
    subject: str,
    message: str,
    is_internal: bool = False,
    flag: str | None = None,
) -> dict:
    """
    Insert a new support ticket and return it.

    Uses ``uuid.uuid1()`` so successive tickets have time-ordered UUIDs.
    """
    db = get_mongo_db()
    now = datetime.now(timezone.utc)
    doc: dict = {
        "ticket_uuid": str(uuid1()),
        "user_id": user_id,
        "subject": subject,
        "message": message,
        "is_internal": is_internal,
        "flag": flag,
        "created_at": now,
    }
    await db.support_tickets.insert_one(doc)
    return _doc_to_ticket(doc)


async def ticket_get_by_uuid(ticket_uuid: str) -> dict | None:
    """
    Fetch a ticket by its public UUID.

    ⚠️  INTENTIONALLY VULNERABLE — no ``user_id`` ownership check.
    Any authenticated caller can retrieve any ticket by guessing/deriving
    a valid UUID (the CTF IDOR sink).
    """
    db = get_mongo_db()
    doc = await db.support_tickets.find_one({"ticket_uuid": ticket_uuid})
    return _doc_to_ticket(doc) if doc else None


async def ticket_list_by_user(user_id: int) -> list[dict]:
    """
    Return all non-internal tickets belonging to the given user.
    This is the *safe* reference pattern (scoped by user_id).
    """
    db = get_mongo_db()
    cursor = db.support_tickets.find(
        {"user_id": user_id, "is_internal": False}
    ).sort("created_at", -1)
    docs = await cursor.to_list(length=200)
    return [_doc_to_ticket(d) for d in docs]
