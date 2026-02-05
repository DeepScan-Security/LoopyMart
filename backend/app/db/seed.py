"""
Database seeding for initial setup.
Seeds admin user (from env vars) and initial category/product data.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.categories_mongo import category_create, category_get_by_slug
from app.db.coupons_mongo import coupon_seed_default
from app.db.products_mongo import product_create, product_list
from app.models.user import User


async def seed_db(db: AsyncSession) -> None:
    """
    Seed the database with initial data.
    
    - Creates admin user if ADMIN_EMAIL and ADMIN_PASSWORD are set in env vars
    - Creates default Electronics category in MongoDB
    - Creates sample product if no products exist
    - Seeds default coupons
    """
    # SQL: Create admin user if credentials are provided
    if settings.admin_email and settings.admin_password:
        result = await db.execute(select(User).where(User.email == settings.admin_email))
        existing_admin = result.scalar_one_or_none()
        if not existing_admin:
            admin_user = User(
                email=settings.admin_email,
                hashed_password=get_password_hash(settings.admin_password),
                full_name=settings.admin_name,
                is_admin=True,
            )
            db.add(admin_user)
            await db.flush()

    # MongoDB: Create default category if it doesn't exist
    cat = await category_get_by_slug("electronics")
    if not cat:
        cat = await category_create(
            name="Electronics",
            slug="electronics",
            description="Electronic gadgets and devices",
        )

    # MongoDB: Create sample product if no products exist
    existing_products = await product_list(limit=1)
    if not existing_products:
        await product_create(
            name="Smartwatch Pro",
            description="Modern smartwatch with multiple color options. Features health tracking, notifications, and a vibrant display.",
            price=12999.00,
            image_url="/dummy-product.png",
            stock=50,
            category_id=cat["id"],
        )

    # MongoDB: Seed default coupons
    await coupon_seed_default()
