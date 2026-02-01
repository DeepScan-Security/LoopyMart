from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.category import Category
from app.models.product import Product
from app.models.user import User


async def seed_db(db: AsyncSession) -> None:
    result = await db.execute(select(User).where(User.email == "admin@example.com"))
    if result.scalar_one_or_none():
        return
    admin_user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("admin123"),
        full_name="Admin",
        is_admin=True,
    )
    db.add(admin_user)
    await db.flush()
    result = await db.execute(select(Category).where(Category.slug == "electronics"))
    if result.scalar_one_or_none():
        return
    cat = Category(name="Electronics", slug="electronics")
    db.add(cat)
    await db.flush()
    result = await db.execute(select(Product).limit(1))
    if result.scalar_one_or_none():
        return
    product = Product(
        name="Smartwatch Pro",
        description="Modern smartwatch with multiple color options. Features health tracking, notifications, and a vibrant display.",
        price=12999.00,
        image_url="/dummy-product.png",
        stock=50,
        category_id=cat.id,
    )
    db.add(product)
    await db.flush()
