"""
LoopyMart API - Main Application

Database Architecture:
- PostgreSQL (SQL): User authentication only
- MongoDB (NoSQL): Products, Categories, Cart, Orders

Authentication: JWT tokens
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import admin, auth, cart, categories, chat, ctf, kyc, orders, payments, products, ratings, spin, wallet
from app.core.config import settings
from app.db.mongo import close_mongo, init_mongo
from app.db.seed import seed_db
from app.db.session import close_db, get_session_maker, init_db
import app.models  # noqa: F401 - register all models with Base.metadata


def get_static_dir() -> Path:
    """Get the static files directory path."""
    return Path(__file__).resolve().parent.parent / settings.static_dir


def get_uploads_dir() -> Path:
    """Get the uploads directory path."""
    return Path(__file__).resolve().parent.parent / settings.uploads_dir


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - handles startup and shutdown."""
    # Validate required settings
    settings.validate_required()

    # Initialize databases
    await init_db()
    await init_mongo()

    # Ensure uploads directory exists
    uploads_dir = get_uploads_dir()
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # Seed initial data
    session_maker = get_session_maker()
    async with session_maker() as db:
        await seed_db(db)
        await db.commit()

    yield

    # Cleanup on shutdown
    await close_db()
    await close_mongo()


app = FastAPI(
    title=settings.app_name,
    description="E-commerce API with JWT authentication. Users in SQL, all other data in MongoDB.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware with configurable origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CTF routes (before static mount so /robots.txt is handled by the app)
app.include_router(ctf.router)

# Mount static files if directory exists
static_dir = get_static_dir()
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include API routers
app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(kyc.router)
app.include_router(chat.router)
app.include_router(ratings.router)
app.include_router(spin.router)
app.include_router(wallet.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}
