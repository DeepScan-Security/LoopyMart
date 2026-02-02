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
