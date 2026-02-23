from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, ASCENDING, DESCENDING

from app.core.config import settings

_client: AsyncIOMotorClient | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    """Get or create MongoDB client singleton."""
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongodb_url)
    return _client


def get_mongo_db():
    """Get the MongoDB database instance."""
    return get_mongo_client()[settings.mongodb_db_name]


async def close_mongo() -> None:
    """Close MongoDB connection."""
    global _client
    if _client is not None:
        _client.close()
        _client = None


async def init_mongo() -> None:
    """
    Initialize MongoDB: verify connection and create indexes.
    
    Collections:
    - products: Product catalog
    - categories: Product categories
    - cart: User shopping carts
    - orders: User orders
    - payments: Payment records
    - coupons: Available coupons
    - coupon_usage: Coupon usage tracking
    - kyc: KYC records
    - chat_history: Support chat history
    - ratings: Product ratings
    """
    db = get_mongo_db()

    # Verify connection
    await db.command("ping")

    # Products collection indexes
    await db.products.create_indexes([
        IndexModel([("category_id", ASCENDING)]),
        IndexModel([("name", ASCENDING)]),
    ])

    # Categories collection indexes
    await db.categories.create_indexes([
        IndexModel([("slug", ASCENDING)], unique=True),
        IndexModel([("name", ASCENDING)]),
    ])

    # Cart collection indexes
    await db.cart.create_indexes([
        IndexModel([("user_id", ASCENDING)]),
        IndexModel([("user_id", ASCENDING), ("product_id", ASCENDING)], unique=True),
    ])

    # Orders collection indexes
    await db.orders.create_indexes([
        IndexModel([("user_id", ASCENDING)]),
        IndexModel([("created_at", DESCENDING)]),
        IndexModel([("status", ASCENDING)]),
    ])

    # Payments collection indexes
    await db.payments.create_indexes([
        IndexModel([("order_id", ASCENDING)]),
        IndexModel([("user_id", ASCENDING)]),
        IndexModel([("created_at", DESCENDING)]),
    ])

    # Coupons collection indexes
    await db.coupons.create_indexes([
        IndexModel([("code", ASCENDING)], unique=True),
        IndexModel([("is_active", ASCENDING)]),
    ])

    # Coupon usage collection indexes
    await db.coupon_usage.create_indexes([
        IndexModel([("user_id", ASCENDING), ("coupon_code", ASCENDING)], unique=True),
    ])

    # KYC collection indexes
    await db.kyc.create_indexes([
        IndexModel([("user_id", ASCENDING)], unique=True),
        IndexModel([("status", ASCENDING)]),
    ])

    # Chat history collection indexes
    await db.chat_history.create_indexes([
        IndexModel([("user_id", ASCENDING)]),
        IndexModel([("created_at", DESCENDING)]),
    ])

    # Ratings collection indexes
    await db.ratings.create_indexes([
        IndexModel([("product_id", ASCENDING)]),
        IndexModel([("user_id", ASCENDING), ("product_id", ASCENDING)], unique=True),
    ])

    # Support Tickets collection indexes (IDOR UUID Sandwich CTF challenge)
    await db.support_tickets.create_indexes([
        IndexModel([("ticket_uuid", ASCENDING)], unique=True),
        IndexModel([("user_id", ASCENDING)]),
        IndexModel([("created_at", DESCENDING)]),
    ])

    # User Addresses collection indexes
    await db.user_addresses.create_indexes([
        IndexModel([("user_id", ASCENDING)]),
        IndexModel([("user_id", ASCENDING), ("is_default", ASCENDING)]),
        IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)]),
    ])
