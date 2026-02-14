# Production deployment (Option A: reverse proxy)

One public host serves the frontend and proxies `/api`, `/static`, and `/robots.txt` to the backend. Users never hit the backend port directly.

## 1. Build frontend

From project root:

```sh
npm run build
```

Use these env vars so the app talks to the same origin (no backend port in the browser):

- `VITE_API_BASE_URL=/api`
- `VITE_STATIC_URL=` (or `/static` for uploads)

If you build without setting them, the defaults in `.env.example` are already correct for this setup.

## 2. Run backend

Run the FastAPI app on port 8001 (only the reverse proxy should connect to it):

```sh
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8001
```

Set `CORS_ORIGINS` to your public origin (e.g. `https://yourapp.com`) if needed.

## 3. Nginx

- Edit [nginx.conf](nginx.conf): set `root` to the path of your built frontend (e.g. `/var/www/earthed/dist`), and in `upstream backend` set the backend address (e.g. `127.0.0.1:8001` or `backend:8001` if backend is another container).
- Install the config and reload nginx.

Result:

- `https://yourapp.com/` → frontend
- `https://yourapp.com/api/*` → backend
- `https://yourapp.com/static/*` → backend
- `https://yourapp.com/robots.txt` → backend (CTF flag)
