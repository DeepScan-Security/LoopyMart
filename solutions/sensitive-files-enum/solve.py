#!/usr/bin/env python3
"""
LoopyMart CTF — Sensitive File & Directory Enumeration
Probes a target server for commonly exposed sensitive files, hidden directories,
version control artifacts, cloud metadata endpoints, and backup files across a
modern Python backend / Vue.js frontend stack.

This is an intentional reconnaissance challenge — certain paths are mocked /
intentionally exposed in the dev environment.

Usage:
    python solutions/sensitive-files-enum/solve.py
    python solutions/sensitive-files-enum/solve.py --url http://localhost:8001
    python solutions/sensitive-files-enum/solve.py --url http://localhost:5173 --concurrency 30
    python solutions/sensitive-files-enum/solve.py --url http://localhost:8001 --show-all
    python solutions/sensitive-files-enum/solve.py --url http://localhost:8001 --extra my_paths.txt
"""

import argparse
import asyncio
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse

try:
    import httpx
except ImportError:
    sys.exit("[!] httpx is required: pip install httpx")


# ─────────────────────────────────────────────────────────────────
#  Default wordlist — grouped for readability
# ─────────────────────────────────────────────────────────────────

PATHS: list[str] = [
    # ── Version Control ────────────────────────────────────────────
    "/.git/",
    "/.git/HEAD",
    "/.git/config",
    "/.git/index",
    "/.git/logs/HEAD",
    "/.git/refs/heads/main",
    "/.git/refs/heads/master",
    "/.git/COMMIT_EDITMSG",
    "/.gitignore",
    "/.gitattributes",
    "/.github/",
    "/.github/workflows/",
    "/.svn/",
    "/.svn/entries",
    "/.svn/wc.db",
    "/.hg/",
    "/.hg/hgrc",
    "/.bzr/",
    "/.bzr/repository/",

    # ── CI / DevOps ─────────────────────────────────────────────────
    "/.gitlab-ci.yml",
    "/.travis.yml",
    "/.circleci/config.yml",
    "/.github/workflows/deploy.yml",
    "/.github/workflows/ci.yml",
    "/Jenkinsfile",
    "/.drone.yml",
    "/bitbucket-pipelines.yml",
    "/.pre-commit-config.yaml",

    # ── Environment / Secrets ──────────────────────────────────────
    "/.env",
    "/.env.local",
    "/.env.production",
    "/.env.staging",
    "/.env.development",
    "/.env.test",
    "/.env.example",
    "/.env.bak",
    "/.env.old",
    "/.env.swp",
    "/.env~",
    "/.flaskenv",
    "/.secrets",
    "/secrets.yml",
    "/secrets.yaml",
    "/secret.key",
    "/.secret",

    # ── App Config ─────────────────────────────────────────────────
    "/config.yml",
    "/config.yaml",
    "/config.json",
    "/config.local.yml",
    "/config.example.yml",
    "/flags.yml",
    "/flags.example.yml",
    "/settings.py",
    "/settings.py.bak",
    "/settings.py.old",
    "/settings.py.swp",
    "/settings.json",
    "/appsettings.json",
    "/application.yml",
    "/application.properties",
    "/web.config",
    "/app.config",
    "/.htaccess",
    "/.htpasswd",
    "/nginx.conf",
    "/uwsgi.ini",
    "/gunicorn.conf.py",
    "/Procfile",
    "/supervisord.conf",

    # ── Python / Backend Artifacts ─────────────────────────────────
    "/requirements.txt",
    "/requirements-dev.txt",
    "/requirements_dev.txt",
    "/Pipfile",
    "/Pipfile.lock",
    "/pyproject.toml",
    "/poetry.lock",
    "/setup.py",
    "/setup.cfg",
    "/tox.ini",
    "/pytest.ini",
    "/mypy.ini",
    "/.python-version",
    "/__pycache__/",
    "/.pytest_cache/",
    "/.mypy_cache/",
    "/.ruff_cache/",
    "/instance/config.py",

    # ── Database / Migrations ──────────────────────────────────────
    "/app.db",
    "/database.db",
    "/db.sqlite3",
    "/dump.sql",
    "/backup.sql",
    "/migrate_db.py",
    "/alembic.ini",
    "/alembic/",

    # ── Vue / Frontend Tooling ─────────────────────────────────────
    "/package.json",
    "/package-lock.json",
    "/yarn.lock",
    "/pnpm-lock.yaml",
    "/.yarnrc",
    "/.yarnrc.yml",
    "/.npmrc",
    "/vite.config.js",
    "/vite.config.ts",
    "/tailwind.config.js",
    "/tailwind.config.ts",
    "/postcss.config.js",
    "/postcss.config.cjs",
    "/jsconfig.json",
    "/tsconfig.json",
    "/tsconfig.node.json",
    "/.babelrc",
    "/babel.config.js",
    "/webpack.config.js",
    "/.eslintrc.js",
    "/.eslintrc.json",
    "/.eslintignore",
    "/.prettierrc",
    "/.prettierignore",
    "/vitest.config.js",
    "/cypress.config.js",
    "/.browserslistrc",

    # ── Built / Distributed Output ─────────────────────────────────
    "/dist/",
    "/dist/index.html",
    "/dist/assets/",
    "/.next/",
    "/.nuxt/",
    "/.output/",
    "/build/",
    "/out/",
    "/public/",

    # ── Container / Orchestration ──────────────────────────────────
    "/docker-compose.yml",
    "/docker-compose.yaml",
    "/docker-compose.override.yml",
    "/Dockerfile",
    "/.dockerignore",
    "/.docker/",
    "/kubernetes/",
    "/k8s/",
    "/.kube/config",
    "/helm/",
    "/charts/",
    "/podman",
    "/podman-compose.yml",

    # ── Infrastructure / IaC ──────────────────────────────────────
    "/.terraform/",
    "/terraform.tfstate",
    "/terraform.tfstate.bak",
    "/terraform.tfvars",
    "/variables.tf",
    "/.ansible/",
    "/inventory.yml",
    "/playbook.yml",
    "/Vagrantfile",

    # ── Cloud Credentials ─────────────────────────────────────────
    "/.aws/credentials",
    "/.aws/config",
    "/.azure/credentials",
    "/.gcloud/credentials.db",

    # ── SSH / Crypto Keys ─────────────────────────────────────────
    "/.ssh/id_rsa",
    "/.ssh/id_ed25519",
    "/.ssh/id_ecdsa",
    "/.ssh/config",
    "/.ssh/authorized_keys",
    "/.ssh/known_hosts",
    "/server.key",
    "/server.pem",
    "/private.pem",
    "/privkey.pem",
    "/cert.pem",
    "/ssl.crt",

    # ── Backup / Swap / Editor Artifacts ──────────────────────────
    "/index.html.bak",
    "/index.html.old",
    "/index.html~",
    "/index.php.bak",
    "/main.py.bak",
    "/main.py.old",
    "/main.py.swp",
    "/main.py~",
    "/app.py.bak",
    "/config.yml.bak",
    "/config.yml.old",
    "/config.yml~",
    "/database.yml.bak",
    "/package.json.bak",
    "/.DS_Store",
    "/Thumbs.db",
    "/.thumbs.db",
    "/.directory",
    "/Desktop.ini",

    # ── Common Admin / Debug Panels ───────────────────────────────
    "/admin",
    "/admin/",
    "/admin/login",
    "/_admin",
    "/dashboard",
    "/debug",
    "/console",
    "/shell",
    "/phpinfo.php",
    "/server-status",
    "/server-info",
    "/__debug__/",
    "/_profiler/",
    "/_debugbar/",
    "/metrics",
    "/health",
    "/healthz",
    "/livez",
    "/readyz",
    "/status",
    "/ping",
    "/actuator/",
    "/actuator/env",
    "/actuator/health",
    "/actuator/info",
    "/actuator/mappings",

    # ── API Docs / OpenAPI ─────────────────────────────────────────
    "/docs",
    "/docs/",
    "/redoc",
    "/openapi.json",
    "/swagger.json",
    "/swagger-ui.html",
    "/api-docs",
    "/v1/",
    "/api/v1/",
    "/api/v2/",

    # ── Log / Dump Files ──────────────────────────────────────────
    "/error.log",
    "/access.log",
    "/app.log",
    "/debug.log",
    "/server.log",
    "/laravel.log",
    "/storage/logs/laravel.log",
    "/tmp/",
    "/logs/",

    # ── Cloud Metadata (IMDSv1 / GCE / Azure IMDS) ─────────────────
    # NOTE: these are absolute URLs probed directly — not joined to base.
    # They are in a separate list (CLOUD_METADATA_PATHS) below.

    # ── Miscellaneous Recon Targets ────────────────────────────────
    "/robots.txt",
    "/humans.txt",
    "/sitemap.xml",
    "/sitemaps/",
    "/.well-known/",
    "/.well-known/security.txt",
    "/.well-known/change-password",
    "/CHANGELOG.md",
    "/CHANGELOG",
    "/CHANGES",
    "/HISTORY.md",
    "/TODO",
    "/TODO.md",
    "/NOTES",
    "/README.md",
    "/README",
    "/LICENSE",
    "/LICENSE.txt",
    "/CONTRIBUTING.md",
    "/COPYING",
    "/.editorconfig",
    "/.clang-format",
]

# Cloud metadata — absolute URLs, probed unconditionally (not joined to base)
CLOUD_METADATA_PATHS: list[str] = [
    # AWS EC2 IMDS
    "http://169.254.169.254/latest/meta-data/",
    "http://169.254.169.254/latest/user-data",
    "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
    # AWS ECS task metadata
    "http://169.254.170.2/v2/metadata",
    # Google Cloud Metadata
    "http://metadata.google.internal/computeMetadata/v1/",
    "http://metadata.google.internal/computeMetadata/v1/instance/",
    "http://metadata.google.internal/computeMetadata/v1/project/project-id",
    # Azure IMDS
    "http://169.254.169.254/metadata/instance?api-version=2021-02-01",
    "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/",
    # Digital Ocean
    "http://169.254.169.254/metadata/v1/",
    "http://169.254.169.254/metadata/v1/id",
    # Alibaba Cloud
    "http://100.100.100.200/latest/meta-data/",
    # Oracle Cloud / Kubernetes
    "http://169.254.169.254/opc/v1/instance/",
    "http://100.96.0.1/api/v1/",
]

# ─────────────────────────────────────────────────────────────────
#  Status classification
# ─────────────────────────────────────────────────────────────────

INTERESTING_STATUSES: set[int] = {
    200, 201, 206, 301, 302, 307, 308,
    401, 403, 405, 500, 501, 503,
}

STATUS_LABELS: dict[int, str] = {
    200: "FOUND",
    206: "FOUND (partial)",
    301: "REDIRECT→",
    302: "REDIRECT→",
    307: "REDIRECT→",
    308: "REDIRECT→",
    401: "UNAUTH (exists)",
    403: "FORBIDDEN (exists)",
    405: "METHOD-NOT-ALLOWED",
    500: "SERVER-ERROR",
    501: "NOT-IMPLEMENTED",
    503: "SERVER-ERROR",
}

# Colours (disabled on non-TTY)
_tty = sys.stdout.isatty()
RED    = "\033[91m" if _tty else ""
GREEN  = "\033[92m" if _tty else ""
YELLOW = "\033[93m" if _tty else ""
CYAN   = "\033[96m" if _tty else ""
BOLD   = "\033[1m"  if _tty else ""
RESET  = "\033[0m"  if _tty else ""


# ─────────────────────────────────────────────────────────────────
#  Result container
# ─────────────────────────────────────────────────────────────────

@dataclass
class Hit:
    url: str
    status: int
    content_type: str
    content_length: int
    snippet: str
    redirect_to: str = ""

    def label(self) -> str:
        return STATUS_LABELS.get(self.status, str(self.status))

    def colour(self) -> str:
        if self.status == 200:
            return GREEN
        if self.status in (401, 403):
            return YELLOW
        if self.status in (301, 302, 307, 308):
            return CYAN
        if self.status >= 500:
            return RED
        return RESET


@dataclass
class ScanResult:
    tested: int = 0
    skipped: int = 0
    errors: int = 0
    hits: list[Hit] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────
#  Probe logic
# ─────────────────────────────────────────────────────────────────

SNIPPET_BYTES = 200


def _build_url(base: str, path: str) -> str:
    """Join base URL + path, handling absolute cloud-metadata URLs."""
    if path.startswith("http://") or path.startswith("https://"):
        return path
    # Ensure clean join (no double-slash)
    return base.rstrip("/") + "/" + path.lstrip("/")


def _short_type(ct: str) -> str:
    """Simplify content-type to a short label."""
    ct = ct.split(";")[0].strip()
    mapping = {
        "application/json": "json",
        "text/html": "html",
        "text/plain": "text",
        "text/xml": "xml",
        "application/xml": "xml",
        "application/octet-stream": "binary",
        "application/javascript": "js",
        "text/css": "css",
        "text/yaml": "yaml",
        "application/x-yaml": "yaml",
    }
    return mapping.get(ct, ct or "?")


async def probe(
    client: httpx.AsyncClient,
    url: str,
    sem: asyncio.Semaphore,
    timeout: float,
) -> Optional[Hit]:
    """Probe a single URL. Returns a Hit if interesting, None if 404."""
    async with sem:
        try:
            resp = await client.get(url, follow_redirects=False, timeout=timeout)
        except Exception:
            try:
                # Fallback to HEAD on connection errors for cloud metadata etc.
                resp = await client.head(url, follow_redirects=False, timeout=timeout)
            except Exception:
                return None  # network error counts as skip

        if resp.status_code == 404:
            return None

        if resp.status_code not in INTERESTING_STATUSES:
            return None

        ct = resp.headers.get("content-type", "")
        cl = int(resp.headers.get("content-length", 0))

        snippet = ""
        if resp.status_code == 200:
            raw = resp.content[:SNIPPET_BYTES]
            try:
                snippet = raw.decode("utf-8", errors="replace").replace("\n", " ").strip()
            except Exception:
                snippet = "<binary>"
        if cl == 0:
            cl = len(resp.content)

        redirect_to = ""
        if resp.status_code in (301, 302, 307, 308):
            redirect_to = resp.headers.get("location", "")

        return Hit(
            url=url,
            status=resp.status_code,
            content_type=_short_type(ct),
            content_length=cl,
            snippet=snippet[:180],
            redirect_to=redirect_to,
        )


# ─────────────────────────────────────────────────────────────────
#  Output helpers
# ─────────────────────────────────────────────────────────────────

def print_hit(hit: Hit) -> None:
    path = "/" + hit.url.split("/", 3)[-1] if not hit.url.startswith("http://169") else hit.url
    col = hit.colour()
    label = hit.label()
    redirect = f"  →  {hit.redirect_to}" if hit.redirect_to else ""
    type_size = f"[{hit.content_type}  {hit.content_length}B]" if hit.content_length else f"[{hit.content_type}]"
    snippet = f'  "{hit.snippet[:100]}"' if hit.snippet else ""
    print(f"  {col}{BOLD}{hit.status}{RESET} {col}{label:<24}{RESET}  {path}{redirect}{type_size}{snippet}")


def print_banner(base: str, total: int) -> None:
    print(f"\n{BOLD}{'═'*66}{RESET}")
    print(f"{BOLD}  Sensitive File & Directory Enumerator{RESET}")
    print(f"  Target : {CYAN}{base}{RESET}")
    print(f"  Probing: {total} paths + {len(CLOUD_METADATA_PATHS)} cloud-metadata targets")
    print(f"{BOLD}{'═'*66}{RESET}\n")


def print_summary(result: ScanResult, elapsed: float) -> None:
    print(f"\n{BOLD}{'─'*66}{RESET}")
    hits_200  = [h for h in result.hits if h.status == 200]
    hits_auth = [h for h in result.hits if h.status in (401, 403)]
    hits_redir = [h for h in result.hits if h.status in (301,302,307,308)]
    hits_other = [h for h in result.hits if h.status not in (200,401,403,301,302,307,308)]

    if result.hits:
        print(f"\n{BOLD}  ── Interesting Paths Found ({len(result.hits)}) ──{RESET}\n")

        if hits_200:
            print(f"  {GREEN}{BOLD}[ Accessible ─ 200 OK ]{RESET}  ({len(hits_200)} hit{'s' if len(hits_200)!=1 else ''})")
            for h in hits_200:
                print_hit(h)
            print()
        if hits_auth:
            print(f"  {YELLOW}{BOLD}[ Exists but Protected ─ 401/403 ]{RESET}  ({len(hits_auth)})")
            for h in hits_auth:
                print_hit(h)
            print()
        if hits_redir:
            print(f"  {CYAN}{BOLD}[ Redirects ─ 3xx ]{RESET}  ({len(hits_redir)})")
            for h in hits_redir:
                print_hit(h)
            print()
        if hits_other:
            print(f"  {RED}{BOLD}[ Other ─ 4xx/5xx ]{RESET}  ({len(hits_other)})")
            for h in hits_other:
                print_hit(h)
            print()
    else:
        print(f"\n  {YELLOW}No interesting paths found.{RESET}\n")

    print(f"{BOLD}{'─'*66}{RESET}")
    print(f"  Tested:  {result.tested}   Hits: {BOLD}{len(result.hits)}{RESET}   "
          f"Skipped/404: {result.tested - len(result.hits)}   "
          f"Errors: {result.errors}   Time: {elapsed:.1f}s")
    print(f"{BOLD}{'═'*66}{RESET}\n")


# ─────────────────────────────────────────────────────────────────
#  Core scan
# ─────────────────────────────────────────────────────────────────

async def scan(
    base_url: str,
    paths: list[str],
    cloud_meta: bool,
    concurrency: int,
    timeout: float,
    show_all: bool,
) -> ScanResult:
    all_paths = list(paths)
    if cloud_meta:
        all_paths += CLOUD_METADATA_PATHS

    urls = [_build_url(base_url, p) for p in paths]
    if cloud_meta:
        urls += CLOUD_METADATA_PATHS  # absolute — not joined

    headers = {
        "User-Agent": "Mozilla/5.0 (sensitive-file-enumerator/1.0)",
        "Accept": "*/*",
    }
    # GCE metadata requires Metadata-Flavor header; others tolerate it gracefully
    gce_headers = {**headers, "Metadata-Flavor": "Google"}

    result = ScanResult()
    sem = asyncio.Semaphore(concurrency)

    print_banner(base_url, len(all_paths))

    async with httpx.AsyncClient(headers=headers, verify=False) as client_default:
        async with httpx.AsyncClient(headers=gce_headers, verify=False) as client_gce:

            async def _probe(url: str) -> Optional[Hit]:
                # Use GCE headers for Google metadata endpoint
                c = client_gce if "metadata.google" in url else client_default
                return await probe(c, url, sem, timeout)

            tasks = [_probe(u) for u in urls]
            total = len(tasks)

            for i, coro in enumerate(asyncio.as_completed(tasks), 1):
                hit = await coro
                result.tested += 1
                if hit:
                    result.hits.append(hit)
                    if show_all or True:  # always print hits live
                        col = hit.colour()
                        print(f"  [{i:>4}/{total}] {col}{hit.status}{RESET}  {hit.url}")
                else:
                    if show_all:
                        print(f"  [{i:>4}/{total}]  404  {urls[i-1]}")

    result.hits.sort(key=lambda h: (h.status != 200, h.status))
    return result


# ─────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────

def load_extra_paths(filepath: str) -> list[str]:
    try:
        lines = Path(filepath).read_text().splitlines()
        return [l.strip() for l in lines if l.strip() and not l.startswith("#")]
    except Exception as e:
        print(f"[!] Could not load extra paths from {filepath}: {e}")
        return []


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Unauthenticated sensitive file & directory enumerator for Python+Vue stacks"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8001",
        help="Target base URL (default: http://localhost:8001)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=20,
        help="Max concurrent requests (default: 20)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Per-request timeout in seconds (default: 5.0)",
    )
    parser.add_argument(
        "--no-cloud-meta",
        action="store_true",
        help="Skip cloud metadata endpoint probes (AWS IMDS, GCE, Azure)",
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Print all paths including 404s (verbose mode)",
    )
    parser.add_argument(
        "--extra",
        metavar="FILE",
        help="Path to a newline-separated file of additional paths to probe",
    )
    args = parser.parse_args()

    # Normalise base URL
    base = args.url.rstrip("/")
    parsed = urlparse(base)
    if not parsed.scheme:
        base = "http://" + base

    paths = list(PATHS)
    if args.extra:
        paths += load_extra_paths(args.extra)

    print(f"{BOLD}[*]{RESET} Starting scan against {CYAN}{base}{RESET}")

    start = time.time()
    try:
        result = asyncio.run(
            scan(
                base_url=base,
                paths=paths,
                cloud_meta=not args.no_cloud_meta,
                concurrency=args.concurrency,
                timeout=args.timeout,
                show_all=args.show_all,
            )
        )
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user.")
        sys.exit(1)

    elapsed = time.time() - start
    print_summary(result, elapsed)

    if result.hits:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
