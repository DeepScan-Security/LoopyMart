from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api import admin, auth, cart, categories, orders, products
from app.db.seed import seed_db
from app.db.session import async_session_maker, init_db
import app.models  # noqa: F401 - register all models with Base.metadata

static_dir = Path(__file__).resolve().parent.parent / "static"
uploads_dir = static_dir / "uploads"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    uploads_dir.mkdir(parents=True, exist_ok=True)
    async with async_session_maker() as db:
        await seed_db(db)
        await db.commit()
    yield


app = FastAPI(
    title="Flipkart Clone API",
    description="E-commerce API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok"}
