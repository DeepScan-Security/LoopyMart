# ─── LoopyMart Backend ───────────────────────────────────────────────────────
# Python 3.12-slim keeps the image lean while shipping pre-built wheels for
# every dependency (asyncpg, cryptography, bcrypt, reportlab, etc.).
# gcc is included only to compile any packages that ship source-only sdists.
FROM python:3.12-slim

WORKDIR /app

# System tools: gcc for any source-only sdists; curl for the health check
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (Docker layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source and the example flags file (used as fallback if
# flags.yml is not bind-mounted at runtime)
COPY app/ ./app/
COPY flags.example.yml .

# Pre-create uploads directory so the mount-point exists even without a volume
RUN mkdir -p static/uploads

# Entrypoint: removes flags.yml if Podman auto-created it as a directory
# (happens when the host file is missing at mount time), so the app falls
# back cleanly to the baked-in flags.example.yml.
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8001

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
