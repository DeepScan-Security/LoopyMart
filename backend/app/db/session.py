"""
SQL Database session management.
Uses MySQL/MariaDB for user authentication only.
All other data (products, categories, cart, orders) is stored in MongoDB.
"""

from urllib.parse import urlparse, urlunparse

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.base import Base


def _get_db_name_and_root_url(database_url: str) -> tuple[str, str]:
    """
    Parse a database URL and return (db_name, url_without_db).
    Supports mysql+aiomysql, postgresql+asyncpg, sqlite variants.
    """
    parsed = urlparse(database_url)
    # path is like '/dbname' — strip the leading slash
    db_name = parsed.path.lstrip("/")
    # Rebuild URL with empty path (root connection)
    root = urlunparse(parsed._replace(path="/"))
    return db_name, root

# Engine will be created lazily
_engine = None
_async_session_maker = None


def get_engine():
    """Get or create the SQLAlchemy async engine."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_pre_ping=True,  # Enable connection health checks
        )
    return _engine


def get_session_maker():
    """Get or create the async session maker."""
    global _async_session_maker
    if _async_session_maker is None:
        _async_session_maker = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _async_session_maker


async def get_db() -> AsyncSession:
    """FastAPI dependency to get a database session."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize the SQL database.
    Creates the database itself if it doesn't exist (MySQL/MariaDB),
    then creates all tables defined in the models.
    """
    db_url = settings.database_url

    # Auto-create the database for MySQL/MariaDB drivers
    if "mysql" in db_url or "mariadb" in db_url:
        db_name, root_url = _get_db_name_and_root_url(db_url)
        if db_name:
            root_engine = create_async_engine(root_url, echo=settings.debug)
            try:
                async with root_engine.begin() as conn:
                    await conn.execute(
                        text(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    )
            finally:
                await root_engine.dispose()

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close the database engine."""
    global _engine, _async_session_maker
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_maker = None


# For backwards compatibility
@property
def async_session_maker():
    return get_session_maker()
