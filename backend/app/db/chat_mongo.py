"""
MongoDB operations for chat history collection.
Chat messages are stored in MongoDB with the following schema:
{
    "_id": ObjectId,
    "user_id": int,
    "message": str,
    "response": str,
    "is_user": bool,
    "created_at": datetime
}
"""

import logging
from datetime import datetime, timezone

import httpx
from bson import ObjectId

from app.core.config import settings
from app.core.flags import get_chat_system_prompt
from app.db.mongo import get_mongo_db

logger = logging.getLogger(__name__)

_FALLBACK_SYSTEM_PROMPT = (
    'You are "EcoBot," a helpful support assistant for an eco-friendly e-commerce store. '
    "Help customers with orders, shipping, products, and general questions. "
    "Be polite, concise, and professional."
)


def _doc_to_chat(doc: dict) -> dict | None:
    """Convert MongoDB document to chat dict with string id."""
    if not doc:
        return None
    out = dict(doc)
    out["id"] = str(out["_id"])
    del out["_id"]
    return out


async def chat_create(user_id: int, message: str, response: str) -> dict:
    """Create a new chat message record."""
    db = get_mongo_db()
    now = datetime.now(timezone.utc)
    doc = {
        "user_id": user_id,
        "message": message,
        "response": response,
        "is_user": True,
        "created_at": now,
    }
    result = await db.chat_history.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _doc_to_chat(doc)


async def chat_get_history(user_id: int, skip: int = 0, limit: int = 50) -> list[dict]:
    """Get chat history for a user."""
    db = get_mongo_db()
    cursor = (
        db.chat_history.find({"user_id": user_id})
        .sort("created_at", 1)
        .skip(skip)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    return [_doc_to_chat(d) for d in docs]


async def generate_ai_response(message: str, history: list[dict] | None = None) -> str:
    """
    Generate an AI response via Ollama (mistral by default).

    Builds a multi-turn message list:
      [system prompt] + [past user/assistant turns] + [current user message]

    Falls back to a polite error string if Ollama is unreachable.
    """
    system_prompt = get_chat_system_prompt() or _FALLBACK_SYSTEM_PROMPT

    messages: list[dict] = [{"role": "system", "content": system_prompt}]

    # Append the most recent 10 exchanges (20 messages) as context
    if history:
        for entry in history[-10:]:
            messages.append({"role": "user", "content": entry["message"]})
            messages.append({"role": "assistant", "content": entry["response"]})

    messages.append({"role": "user", "content": message})

    payload = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{settings.ollama_url.rstrip('/')}/api/chat",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["message"]["content"]
    except httpx.ConnectError:
        logger.warning("Ollama is not reachable at %s", settings.ollama_url)
        return (
            "I'm having trouble connecting to the AI service right now. "
            "Please try again in a moment or contact support directly."
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Ollama request failed: %s", exc)
        return (
            "Sorry, I encountered an unexpected error. "
            "Please try again or contact our support team."
        )
