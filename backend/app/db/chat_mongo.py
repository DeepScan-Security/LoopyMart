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

from datetime import datetime, timezone

from bson import ObjectId

from app.db.mongo import get_mongo_db


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


def generate_ai_response(message: str) -> str:
    """Generate a dummy AI response based on the message."""
    message_lower = message.lower()
    
    # Rule-based responses
    if "order" in message_lower and "track" in message_lower:
        return "You can track your order from the Orders page. Click on your profile icon and select 'My Orders' to view all your orders and their current status."
    
    if "cancel" in message_lower:
        return "To cancel an order, go to My Orders, select the order you want to cancel, and click on the 'Cancel Order' button. Note that orders can only be cancelled before they are shipped."
    
    if "return" in message_lower or "refund" in message_lower:
        return "Our return policy allows returns within 7 days of delivery. To initiate a return, go to My Orders, select the order, and click 'Return Item'. Refunds are processed within 5-7 business days."
    
    if "payment" in message_lower or "pay" in message_lower:
        return "We accept multiple payment methods including Credit/Debit Cards, UPI, Wallet, and Cash on Delivery. Your payment information is securely encrypted."
    
    if "delivery" in message_lower or "shipping" in message_lower:
        return "Standard delivery takes 5-7 business days. Express delivery (available for select products) takes 2-3 business days. Flipkart Black members get free express delivery on all orders!"
    
    if "wallet" in message_lower:
        return "Your wallet balance can be used for purchases at checkout. You can add money to your wallet or earn cashback through various offers and the spin wheel feature!"
    
    if "coupon" in message_lower or "discount" in message_lower:
        return "Check out the available coupons on the checkout page. New users get exclusive coupons worth ₹100 each! Remember, each coupon can only be used once."
    
    if "black" in message_lower or "membership" in message_lower:
        return "Flipkart Black is our premium membership program offering exclusive benefits like free express delivery, early access to sales, and special discounts. Upgrade from your profile page!"
    
    if "account" in message_lower or "profile" in message_lower:
        return "You can update your profile information, including name, phone, and address from the Profile section. Click on your profile icon to access settings."
    
    if "hello" in message_lower or "hi" in message_lower or "hey" in message_lower:
        return "Hello! I'm your Flipkart support assistant. How can I help you today? You can ask me about orders, payments, returns, delivery, or any other questions!"
    
    if "thank" in message_lower:
        return "You're welcome! Is there anything else I can help you with?"
    
    # Default response
    return "Thank you for contacting Flipkart support. I can help you with orders, payments, returns, delivery, wallet, coupons, and account management. Please feel free to ask your question, and I'll do my best to assist you!"
