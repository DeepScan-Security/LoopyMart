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
from app.models.user import User


def _fix_sqlalchemy_url(url: str, default_db: str = "loopymart") -> tuple[str, str, str]:
    """
    Ensure standard driver prefixes point to async drivers.
    Returns: (Full DB URL, DB Name, Root URL without DB)
    """
    from urllib.parse import urlparse, urlunparse

    if url.startswith("mysql://"):
        url = url.replace("mysql://", "mysql+aiomysql://", 1)
    elif url.startswith("mariadb://"):
        url = url.replace("mariadb://", "mysql+aiomysql://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    parsed = urlparse(url)
    db_name = parsed.path.lstrip("/")
    
    if not db_name and ("mysql" in url or "postgresql" in url):
        db_name = default_db
        parsed = parsed._replace(path=f"/{db_name}")

    full_url = urlunparse(parsed)
    root_url = urlunparse(parsed._replace(path="/"))

    return full_url, db_name, root_url

# Engine will be created lazily
_engine = None
_async_session_maker = None


def get_engine():
    """Get or create the SQLAlchemy async engine."""
    global _engine
    if _engine is None:
        db_url, _, _ = _fix_sqlalchemy_url(settings.database_url)
        _engine = create_async_engine(
            db_url,
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
    db_url, db_name, root_url = _fix_sqlalchemy_url(settings.database_url)

    # Auto-create the database for MySQL/MariaDB drivers
    if "mysql" in db_url or "mariadb" in db_url:
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
