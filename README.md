# LoopyMart

A minimal yet scalable e-commerce app with Vue 3 frontend and FastAPI backend.

## Features

- **User/Admin authentication** (JWT)
- **Home page** with featured products and categories
- **Product listing** with category filters and search
- **Product detail** with add-to-cart
- **Cart** and **Checkout**
- **Order history**
- **Admin**: upload/manage products and categories
- **Payment Gateway**: Razorpay integration (optional)

## Tech Stack

- **Frontend**: Vue 3, Vue Router, Axios, Vite (Node 20+ required)
- **Backend**: Python 3.10+, FastAPI, JWT authentication, bcrypt

## Database Architecture

| Data | Database | Description |
|------|----------|-------------|
| **Users** | PostgreSQL (SQL) | User authentication and profiles |
| **Products** | MongoDB (NoSQL) | Product catalog |
| **Categories** | MongoDB (NoSQL) | Product categories |
| **Cart** | MongoDB (NoSQL) | Shopping cart items |
| **Orders** | MongoDB (NoSQL) | Order history |

This hybrid approach uses:
- **PostgreSQL** for user data (ACID compliance, secure authentication)
- **MongoDB** for product/catalog data (flexible schema, easy scaling)

## Project Structure

```
LoopyMart/
├── backend/              # FastAPI app
│   ├── app/
│   │   ├── api/          # Routes (auth, categories, products, cart, orders, admin)
│   │   ├── core/         # Config, security
│   │   ├── db/           # Database operations (SQL + MongoDB)
│   │   ├── models/       # SQLAlchemy models (User only)
│   │   └── schemas/      # Pydantic schemas
│   ├── .env.example      # Environment variables template
│   └── requirements.txt
├── public/               # Static assets
├── src/
│   ├── api/              # API client
│   ├── components/
│   ├── router/
│   └── views/
├── .env.example          # Frontend environment template
└── package.json
```

## Setup

### Prerequisites

- **Python 3.10+**
- **Node.js 20+**
- **PostgreSQL** (for user data)
- **MongoDB** (for product/catalog data)

### 1. Backend Setup

```sh
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your database credentials and secret key
```

#### Required Environment Variables

```env
# PostgreSQL (for users)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/loopymart_users

# MongoDB (for products, categories, cart, orders)
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=loopymart

# JWT Secret Key (generate a strong random key)
SECRET_KEY=your-secret-key-here

# Admin credentials for initial setup (optional)
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=secure-password
```

#### Start the Backend

```sh
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

Backend runs at **http://127.0.0.1:8001**

### 2. Frontend Setup

```sh
# From project root
npm install

# Copy and configure environment variables (optional)
cp .env.example .env.local
# Edit .env.local if needed

npm run dev
```

Frontend runs at **http://localhost:5173** and proxies `/api` to the backend.

### 3. Database Setup

**PostgreSQL:**
```sh
createdb loopymart_users
```
Tables are created automatically on first start.

**MongoDB:**
Ensure MongoDB is running on `localhost:27017`. Collections and indexes are created automatically.

## Environment Variables

### Backend (`.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection URL |
| `MONGODB_URL` | Yes | - | MongoDB connection URL |
| `MONGODB_DB_NAME` | Yes | - | MongoDB database name |
| `SECRET_KEY` | Yes | - | JWT signing key |
| `ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `10080` | Token expiry (7 days) |
| `CORS_ORIGINS` | No | `localhost:5173` | Allowed CORS origins |
| `ADMIN_EMAIL` | No | - | Initial admin email |
| `ADMIN_PASSWORD` | No | - | Initial admin password |
| `RAZORPAY_KEY_ID` | No | - | Razorpay API key |
| `RAZORPAY_KEY_SECRET` | No | - | Razorpay secret |

### Frontend (`.env.local`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_URL` | No | `http://127.0.0.1:8001` | Backend URL for dev proxy |
| `VITE_API_BASE_URL` | No | `/api` | API base URL |
| `VITE_STATIC_URL` | No | - | Static files URL |

## Payment Gateway (Razorpay)

To enable online payments, add to `.env`:
```env
RAZORPAY_KEY_ID=rzp_test_xxxx
RAZORPAY_KEY_SECRET=your_secret
```

Get test keys from [Razorpay Dashboard](https://dashboard.razorpay.com/).

If not configured, "Place Order" creates orders without payment (COD flow).

## API Overview

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login |
| GET | `/auth/me` | Current user (auth) |
| GET | `/categories` | List categories |
| GET | `/categories/{slug}` | Get category by slug |
| GET | `/products` | List products (`category_slug`, `q`, `skip`, `limit`) |
| GET | `/products/{id}` | Product detail |
| GET/POST/PATCH/DELETE | `/cart` | Cart operations (auth) |
| GET/POST | `/orders` | Orders (auth) |
| POST | `/orders/create-payment` | Create Razorpay order (auth) |
| POST | `/orders/verify-payment` | Verify payment (auth) |
| GET | `/admin/orders` | List all orders (admin) |
| POST/PUT/DELETE | `/admin/categories`, `/admin/products` | Admin CRUD |
| POST | `/admin/upload` | Upload image (admin) |

## Build for Production

```sh
# Frontend
npm run build
# Serve dist/ with any static server

# Backend
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

Set production environment variables and configure CORS origins appropriately.

### Production with reverse proxy (Option A)

To expose one URL to users (frontend, API, and `/robots.txt` on the same host, backend port not public):

1. Build the frontend with `VITE_API_BASE_URL=/api` and `VITE_STATIC_URL=` (see [.env.example](.env.example)).
2. Run the backend on port 8001 (only the proxy should connect to it).
3. Put a reverse proxy in front: serve the built `dist/` at `/`, and proxy `/api`, `/static`, and `/robots.txt` to the backend.

See **[deploy/README.md](deploy/README.md)** and **[deploy/nginx.conf](deploy/nginx.conf)** for an nginx-based setup.

## Security Notes

- Never commit `.env` files to version control
- Use strong, unique `SECRET_KEY` in production
- Configure CORS origins for your production domain
- Use HTTPS in production
- Admin credentials in env vars are for initial setup only
