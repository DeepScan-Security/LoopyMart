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
from fastapi import APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import addresses, admin, auth, cart, categories, chat, ctf, kyc, mock_sensitive, orders, payments, products, ratings, seller, spin, tickets, vendor, wallet, wishlist
from app.core.config import settings
from app.core.flags import get_flag
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

    # Write SSRF challenge flag to a "sensitive" file on the filesystem.
    # Contestants reach this via file:///tmp/ssrf_flag.txt through the
    # vulnerable invoice-template-URL fetch endpoint.
    try:
        ssrf_flag = get_flag("ssrf_invoice")
        # Write blank content when hidden so SSRF path still resolves the file
        # but returns nothing that reveals a flag.
        Path("/tmp/ssrf_flag.txt").write_text(ssrf_flag if ssrf_flag else "")
    except Exception:
        pass  # Non-fatal — don't crash startup if flags.yml is missing

    # Write Path Traversal challenge flag to a predictable filesystem path.
    # Contestants reach this via GET /auth/profile-picture?filename=../../../../../../tmp/path_traversal_flag.txt
    try:
        pt_flag = get_flag("path_traversal")
        Path("/tmp/path_traversal_flag.txt").write_text(pt_flag if pt_flag else "")
    except Exception:
        pass  # Non-fatal — don't crash startup if flags.yml is missing

    # Initialise vendor directory-listing / path-traversal challenge data.
    # Creates /tmp/vendor_data/{slug}.txt files and /tmp/vendor_traversal_flag.txt
    try:
        vendor.init_vendor_data()
    except Exception:
        pass  # Non-fatal

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
# Mock sensitive files — honeypot routes for enumeration CTF challenge
app.include_router(mock_sensitive.router)
# Vendor directory-listing / path-traversal CTF challenge
app.include_router(vendor.router)

# Mount static files if directory exists
static_dir = get_static_dir()
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include API routers
api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(categories.router)
api_router.include_router(products.router)
api_router.include_router(cart.router)
api_router.include_router(orders.router)
api_router.include_router(payments.router)
api_router.include_router(kyc.router)
api_router.include_router(seller.router)
api_router.include_router(chat.router)
api_router.include_router(ratings.router)
api_router.include_router(spin.router)
api_router.include_router(wallet.router)
api_router.include_router(wishlist.router)
api_router.include_router(tickets.router)
api_router.include_router(addresses.router)
api_router.include_router(admin.router)

app.include_router(api_router)


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}
