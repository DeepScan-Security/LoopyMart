# Sensitive File & Directory Enumeration

**Category:** Recon / Information Disclosure  
**Difficulty:** Easy–Medium  
**Target Stack:** Python (FastAPI) backend + Vue 3 frontend  

---

## Description

Modern web applications built on Python + Vue/Vite often inadvertently expose
a range of files that a developer considers "not public" but are served
statically or left accessible due to misconfigured hosting, a missing
`.gitignore`, or a developer forgetting to restrict routes.

This script probes a target server for a wide range of path families:

| Category | Examples |
|---|---|
| Version control | `/.git/HEAD`, `/.git/config`, `/.svn/`, `/.hg/` |
| CI / DevOps | `/.gitlab-ci.yml`, `/.travis.yml`, `/Jenkinsfile` |
| Env / secrets | `/.env`, `/.env.local`, `/.env.bak`, `/secrets.yml`, `/.htpasswd` |
| App config | `/config.yml`, `/flags.yml`, `/config.local.yml`, `/settings.py` |
| Python artifacts | `/requirements.txt`, `/pyproject.toml`, `/poetry.lock`, `/__pycache__/` |
| Vue / tooling | `/package.json`, `/vite.config.js`, `/tailwind.config.js`, `/.npmrc` |
| Build output | `/dist/`, `/.next/`, `/.nuxt/`, `/build/` |
| Container / IaC | `/docker-compose.yml`, `/.terraform/`, `/terraform.tfstate`, `/.kube/config` |
| Cloud credentials | `/.aws/credentials`, `/.azure/credentials`, `/.ssh/id_rsa` |
| Cloud metadata IMDSv1 | `http://169.254.169.254/latest/meta-data/`, GCE, Azure IMDS |
| Backup / swap / editor | `/.env.bak`, `/config.yml.old`, `/main.py.swp`, `/.DS_Store` |
| Admin / debug panels | `/admin`, `/docs`, `/_debugbar/`, `/actuator/env`, `/metrics` |
| Log & dump files | `/error.log`, `/dump.sql`, `/app.db`, `/db.sqlite3` |

---

## Setup

```bash
pip install httpx
```

---

## Usage

```bash
# Probe the backend (default: http://localhost:8001)
python solutions/sensitive-files-enum/solve.py

# Probe the Vite dev server
python solutions/sensitive-files-enum/solve.py --url http://localhost:5173

# Higher concurrency for faster sweeps
python solutions/sensitive-files-enum/solve.py --url http://localhost:8001 --concurrency 40

# Skip cloud metadata probes (faster, no external network)
python solutions/sensitive-files-enum/solve.py --no-cloud-meta

# Verbose — show all 404s too
python solutions/sensitive-files-enum/solve.py --show-all

# Append your own wordlist
python solutions/sensitive-files-enum/solve.py --extra custom_paths.txt
```

### CLI Arguments

| Argument | Default | Description |
|---|---|---|
| `--url` | `http://localhost:8001` | Target base URL |
| `--concurrency` | `20` | Max concurrent requests |
| `--timeout` | `5.0` | Per-request timeout (seconds) |
| `--no-cloud-meta` | off | Skip AWS/GCE/Azure IMDS probes |
| `--show-all` | off | Print every result including 404s |
| `--extra FILE` | — | Extra wordlist file (one path per line) |

---

## Example Output

```
══════════════════════════════════════════════════════════════════
  Sensitive File & Directory Enumerator
  Target : http://localhost:8001
  Probing: 175 paths + 14 cloud-metadata targets
══════════════════════════════════════════════════════════════════

  [ 12/189]  200  http://localhost:8001/robots.txt
  [ 23/189]  200  http://localhost:8001/docs
  [ 31/189]  401  http://localhost:8001/admin
  [ 44/189]  200  http://localhost:8001/openapi.json
  ...

  ── Interesting Paths Found (6) ──

  [ Accessible ─ 200 OK ]  (4 hits)
  200 FOUND                   /robots.txt       [text  212B]  "User-agent: * Disallow: ..."
  200 FOUND                   /docs             [html  848B]  "<!DOCTYPE html><html> ..."
  200 FOUND                   /openapi.json     [json  9843B] "{"openapi":"3.1.0","info" ..."
  200 FOUND                   /health           [json  14B]   "{"status":"ok"}"

  [ Exists but Protected ─ 401/403 ]  (2)
  401 UNAUTH (exists)          /admin            [json  32B]
  403 FORBIDDEN (exists)       /flag.txt         [json  27B]

──────────────────────────────────────────────────────────────────
  Tested: 189   Hits: 6   Skipped/404: 183   Errors: 0   Time: 4.3s
══════════════════════════════════════════════════════════════════
```

---

## Interpreting Results

| Status | Meaning |
|---|---|
| `200 FOUND` | File/path is publicly accessible — read its content immediately |
| `401 UNAUTH` | Path exists and requires authentication — note for later |
| `403 FORBIDDEN` | Path exists but access is denied — still reveals presence |
| `301/302/307` | Redirects — follow to see if the final destination is accessible |
| `405` | Method not allowed but resource exists |
| `500` | Server error when handling the path — may indicate an internal resource |

**High-value 200s to investigate manually:**
- `/.env` — may contain `DATABASE_URL`, `SECRET_KEY`, API tokens
- `/.git/config` — exposes remote URL (private repo URL, credentials in URL)
- `/requirements.txt` — reveals exact dependency versions for known CVEs
- `/flags.yml` or `/config.local.yml` — CTF flags / production secrets
- `/terraform.tfstate` — contains plaintext credentials and infra details
- `/openapi.json` — maps the entire API surface

---

## What LoopyMart Exposes in Dev

When running both Vite `:5173` and uvicorn `:8001` locally, the following paths
are expected to respond:

| Path | Port | Status | Reason |
|---|---|---|---|
| `/robots.txt` | `:8001` | `200` | Intentionally exposed (CTF Challenge 1) |
| `/docs` | `:8001` | `200` | FastAPI interactive docs mounted by default |
| `/openapi.json` | `:8001` | `200` | FastAPI schema, always public |
| `/health` | `:8001` | `200` | `GET /health` → `{"status":"ok"}` |
| `/flag.txt` | `:8001` | `403` | CTF SSRF target — blocks external callers |
| `/admin` | `:8001` | `401` | Admin panel, JWT-gated |
| `/package.json` | `:5173` | `200` | Vite serves root files statically in dev |
| `/vite.config.js` | `:5173` | `200` | Vite source in dev root — readable |
| `/index.html` | both | varies | Root HTML |

---

## Custom Wordlist Format

Pass `--extra path/to/wordlist.txt`. Format:

```
# lines starting with # are ignored
/admin/login
/.env.prod
/api/v1/internal
/static/debug.js
```

---

## Mitigation Guidance

- **Restrict static serving**: In both Vite and nginx, only serve files from
  `dist/` or `public/`; never the project root.
- **Remove `/docs` and `/openapi.json` in production**:
  ```python
  app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
  ```
- **Gitignore sensitive files**: `.env`, `flags.yml`, `config.local.yml`,
  `*.bak`, `*.swp`, `*.old` should all be in `.gitignore`.
- **Disable IMDS v1 on cloud VMs**: Use IMDSv2 (AWS) or require metadata
  service account restrictions (GCE/Azure).
- **HTTP 404 for all non-routes** on the API server — never return 403 for
  paths that shouldn't be known to exist.
- **Rotate all credentials** if any `.env` or config file was found accessible.
