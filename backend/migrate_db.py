"""
Database migration script to recreate users table with updated schema.
WARNING: This will DELETE ALL USER DATA!
Only use in development.
"""

import asyncio
from app.core.config import settings
from app.db.session import get_engine
from app.models.base import Base
from app.models.user import User  # noqa: F401 - Import to register the model


async def migrate():
    """Drop and recreate users table with new schema."""
    engine = get_engine()
    
    print("=" * 70)
    print("DATABASE MIGRATION - RECREATE USERS TABLE")
    print("=" * 70)
    print(f"Database: {settings.database_url[:50]}...")
    print("\nWARNING: This will DELETE ALL USER DATA!")
    print("Only proceed in development environment.")
    print("=" * 70)
    
    response = input("\nType 'yes' to proceed: ")
    if response.lower() != 'yes':
        print("Migration cancelled.")
        return
    
    print("\n[1/3] Dropping existing users table...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all, tables=[User.__table__])
    print("✓ Users table dropped")
    
    print("\n[2/3] Creating users table with new schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[User.__table__])
    print("✓ Users table created with updated schema")
    
    print("\n[3/3] Cleaning up...")
    await engine.dispose()
    print("✓ Complete")
    
    print("\n" + "=" * 70)
    print("MIGRATION SUCCESSFUL!")
    print("=" * 70)
    print("\nThe users table has been recreated with the new schema.")
    print("All previous user data has been deleted.")
    print("\nNext steps:")
    print("1. Restart your application: npm run dev:all")
    print("2. The seed script will create a new admin user")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(migrate())
