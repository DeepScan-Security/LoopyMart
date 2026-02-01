# Flipkart Clone

A minimal yet scalable Flipkart-like e-commerce app with Vue 3 frontend and FastAPI backend.

## Features

- **User/Admin authentication** (JWT)
- **Home page** with featured products and categories
- **Product listing** with category filters
- **Product detail** with add-to-cart
- **Cart** and **Checkout**
- **Order history**
- **Admin**: upload/manage products and categories

## Tech Stack

- **Frontend**: Vue 3, Vue Router, Axios, Vite (Node 20+ required for build)
- **Backend**: Python 3.10+, FastAPI, SQLAlchemy (async), SQLite, JWT, bcrypt

## Project Structure

```
Flipkart-clone/
├── backend/           # FastAPI app
│   ├── app/
│   │   ├── api/      # Routes (auth, categories, products, cart, orders, admin)
│   │   ├── core/     # Config, security
│   │   ├── db/       # Session, seed
│   │   ├── models/   # SQLAlchemy models
│   │   └── schemas/  # Pydantic schemas
│   └── requirements.txt
├── public/           # Static assets (e.g. dummy-product.png)
├── src/
│   ├── api/          # API client
│   ├── components/
│   ├── router/
│   └── views/
└── package.json
```

## Run Locally

### 1. Backend

```sh
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# If pip has SSL issues: pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Backend runs at **http://127.0.0.1:8001**. DB and seed (admin user + sample product) are created on first start.

### 2. Frontend

Requires Node 20+ (see `package.json` engines). If you have Node 18, upgrade or use `nvm use 20`.

```sh
npm install
npm run dev
```

Frontend runs at **http://localhost:5173** and proxies `/api` to the backend.

### 3. Default credentials

- **Admin**: `admin@example.com` / `admin123`
- Register a new user for customer flow.

## API Overview

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Register |
| POST | `/auth/login` | Login |
| GET | `/auth/me` | Current user (auth) |
| GET | `/categories` | List categories |
| GET | `/categories/{slug}` | Get category by slug |
| GET | `/products` | List products (query: `category_slug`, `skip`, `limit`) |
| GET | `/products/{id}` | Product detail |
| GET/POST/PATCH/DELETE | `/cart`, `/cart/{id}` | Cart (auth) |
| GET/POST | `/orders`, `/orders` | Orders (auth) |
| POST/PUT/DELETE | `/admin/categories`, `/admin/products` | Admin CRUD |
| POST | `/admin/upload` | Upload image (admin) |

## Build for production

```sh
npm run build
# Serve dist/ with any static server; point API base URL to your backend.
```
