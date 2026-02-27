"""
[INTENTIONALLY VULNERABLE – CTF Challenge: vendor_traversal]

Publicly accessible vendor directory service with two deliberate weaknesses:

1. Directory listing enabled (CWE-548)
   GET /vendor         — Apache-style HTML index of all vendor folders on disk.
   GET /vendor/<name>/ — contents of that vendor folder.
   The listing includes a normal-looking internal folder ("internal-ops") whose
   contents expose a flag.txt file that holds the CTF flag.

2. Path traversal (CWE-22)
   GET /vendor/{path}  joins the caller-supplied path directly to the vendor data
   directory with NO Path.resolve() call and NO boundary check.  Supplying "../"
   sequences lets an attacker escape the vendor data root and read arbitrary files
   the server process can access.

CTF Goal:
  Option A — directory listing recon:
    GET /vendor  → spot "internal-ops/" → GET /vendor/internal-ops/ → find flag.txt
                → GET /vendor/internal-ops/flag.txt → flag

  Option B — path traversal (classic):
    GET /vendor/../vendor_traversal_flag.txt  → flag written to /tmp/ on startup

CWE-548  Information Exposure Through Directory Listing
CWE-22   Improper Limitation of a Pathname to a Restricted Directory
"""

import random
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import HTMLResponse, PlainTextResponse

from app.core.flags import get_flag

router = APIRouter(tags=["vendor"])

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Large pool of realistic-looking mock vendor slugs; a random subset is
# sampled at startup so the listing differs between deployments.
_VENDOR_POOL: list[tuple[str, str]] = [
    ("TechCorp", "techcorp"),
    ("EcoGoods", "ecogoods"),
    ("BluePeak Supplies", "bluepeak-supplies"),
    ("NovaStar Trading", "novastar-trading"),
    ("GreenBay Co.", "greenbay"),
    ("Sunrise Tech Ltd.", "sunrise-tech"),
    ("Omega Supplies", "omega-supplies"),
    ("Redwood Goods", "redwood-goods"),
    ("Prime Catalogue", "prime-catalogue"),
    ("ZephyrCorp", "zephyrcorp"),
    ("Horizon Imports", "horizon-imports"),
    ("SilverCrest", "silvercrest"),
    ("Apex Distributors", "apex-distributors"),
    ("ClearPath Exports", "clearpath-exports"),
    ("United Wholesale", "united-wholesale"),
    ("DeltaSource", "deltasource"),
    ("Pinnacle Goods", "pinnacle-goods"),
    ("TrueNorth Trading", "truenorth-trading"),
]

_VENDOR_SAMPLE_COUNT = 10  # How many mock vendors to include per deployment.

# The "flag vendor" — normal-looking folder; contains a hidden flag.txt inside.
_FLAG_VENDOR_DISPLAY = "InternalOps Inc."
_FLAG_VENDOR_SLUG    = "internal-ops"

# Vendor data lives in /tmp so it is rebuilt on every server restart.
_VENDOR_DATA_DIR = Path("/tmp/vendor_data")


# ---------------------------------------------------------------------------
# Startup helper (called from main.py lifespan)
# ---------------------------------------------------------------------------

def init_vendor_data() -> None:
    """
    Build /tmp/vendor_data/ as a directory tree of vendor folders.

    Layout after init:
        /tmp/vendor_data/
            techcorp/
                profile.txt        <- mock vendor details
            ecogoods/
                profile.txt
            ...  (random sample of _VENDOR_SAMPLE_COUNT vendors from _VENDOR_POOL)
            internal-ops/          <- the flag vendor (looks normal in listing)
                flag.txt           <- contains the CTF flag

    Also writes /tmp/vendor_traversal_flag.txt at the /tmp root so classic
    path-traversal payloads like  ../vendor_traversal_flag.txt  work too.

    Called once during FastAPI startup — safe to call multiple times (idempotent).
    """
    _VENDOR_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Sample a random subset of mock vendors (stable once folders exist on disk).
    selected = random.sample(_VENDOR_POOL, k=min(_VENDOR_SAMPLE_COUNT, len(_VENDOR_POOL)))

    for display_name, slug in selected:
        vendor_dir = _VENDOR_DATA_DIR / slug
        vendor_dir.mkdir(exist_ok=True)
        profile = vendor_dir / "profile.txt"
        if not profile.exists():
            profile.write_text(
                f"Vendor:   {display_name}\n"
                f"Slug:     {slug}\n"
                f"Status:   Active\n"
                f"Category: General Merchandise\n"
                f"Contact:  vendors@loopymart.local\n"
            )

    # Create the flag vendor folder with an internal flag.txt.
    flag = get_flag("vendor_traversal") or "CTF{flag_not_configured}"
    flag_vendor_dir = _VENDOR_DATA_DIR / _FLAG_VENDOR_SLUG
    flag_vendor_dir.mkdir(exist_ok=True)
    (flag_vendor_dir / "flag.txt").write_text(flag + "\n")

    # /tmp/vendor_traversal_flag.txt — reachable via one-level traversal.
    try:
        Path("/tmp/vendor_traversal_flag.txt").write_text(flag + "\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# HTML helper
# ---------------------------------------------------------------------------

_CSS = """
    body  { font-family: monospace; }
    h1    { border-bottom: 1px solid #aaa; padding-bottom: 4px; }
    table { border-collapse: collapse; }
    th, td { padding: 2px 16px 2px 0; text-align: left; }
    tr:hover { background: #f5f5f5; }
    address { margin-top: 12px; font-style: italic; color: #888; font-size: 0.85em; }
"""


def _listing_html(title: str, parent_href: str, entries: list[tuple[str, str, str]]) -> str:
    """Render an Apache-style directory listing page."""
    rows = [
        f"    <tr>\n"
        f"      <td><a href=\"{parent_href}\">Parent Directory</a></td>\n"
        f"      <td></td><td>-</td>\n"
        f"    </tr>"
    ]
    for href, name, size in entries:
        rows.append(
            f"    <tr>\n"
            f"      <td><a href=\"{href}\">{name}</a></td>\n"
            f"      <td>2026-02-27 00:00</td>\n"
            f"      <td>{size}</td>\n"
            f"    </tr>"
        )
    rows_html = "\n".join(rows)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>{title}</title>
  <style>{_CSS}</style>
</head>
<body>
  <h1>{title}</h1>
  <table>
    <tr><th>Name</th><th>Last modified</th><th>Size</th></tr>
{rows_html}
  </table>
  <address>LoopyMart Vendor Service/1.4.2</address>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# GET /vendor — top-level directory listing (reads real filesystem)
# ---------------------------------------------------------------------------

@router.get("/vendor", response_class=HTMLResponse, include_in_schema=True)
def vendor_directory_listing() -> str:
    """
    [INTENTIONALLY VULNERABLE – CWE-548: Directory Listing Enabled]

    Reads /tmp/vendor_data/ from disk and returns a live Apache-style HTML
    directory index of every vendor folder present.

    The listing is driven by actual filesystem entries — whatever folders exist
    in /tmp/vendor_data/ are shown here, including the "internal-ops/" folder
    that should never be publicly visible.

    No authentication required.
    """
    if not _VENDOR_DATA_DIR.exists():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Vendor data not initialised.")

    entries: list[tuple[str, str, str]] = []
    for child in sorted(_VENDOR_DATA_DIR.iterdir()):
        if child.is_dir():
            entries.append((f"/vendor/{child.name}/", f"{child.name}/", "-"))
        else:
            entries.append((f"/vendor/{child.name}", child.name, str(child.stat().st_size)))

    random.shuffle(entries)  # shuffle to avoid ordering clues
    return _listing_html("Index of /vendor", "/", entries)


# ---------------------------------------------------------------------------
# GET /vendor/{path} — sub-directory listing or file read (traversal sink)
# ---------------------------------------------------------------------------

@router.get("/vendor/{vendor_path:path}")
def serve_vendor_path(vendor_path: str):  # type: ignore[return]
    """
    [INTENTIONALLY VULNERABLE – CWE-22: Path Traversal]

    Serves either a sub-directory listing or a raw file from the vendor tree.

    `vendor_path` is joined directly to the vendor data root with the Python
    `/` (Path.__truediv__) operator.  No resolve() / is_relative_to() check is
    performed, so `..` sequences freely escape the vendor data root.

    Normal access patterns:
      GET /vendor/techcorp/
          → HTML listing of /tmp/vendor_data/techcorp/  (shows profile.txt)

      GET /vendor/techcorp/profile.txt
          → plain text vendor profile

      GET /vendor/internal-ops/
          → HTML listing showing flag.txt (recon path)

      GET /vendor/internal-ops/flag.txt
          → the CTF flag value

    Path traversal:
      GET /vendor/../vendor_traversal_flag.txt
          → /tmp/vendor_traversal_flag.txt

      GET /vendor/../../etc/passwd
          → /etc/passwd

    [INTENTIONALLY VULNERABLE – CTF challenge path-traversal sink]
    """
    # Strip surrounding slashes for clean Path joining.
    clean = vendor_path.strip("/")

    # VULNERABILITY: no canonicalisation or boundary check.
    target = _VENDOR_DATA_DIR / clean  # ← intentional traversal sink

    # --- directory: render sub-listing ---
    if target.is_dir():
        entries: list[tuple[str, str, str]] = []
        try:
            for child in sorted(target.iterdir()):
                if child.is_dir():
                    entries.append((f"/vendor/{clean}/{child.name}/", f"{child.name}/", "-"))
                else:
                    entries.append((f"/vendor/{clean}/{child.name}",
                                    child.name, str(child.stat().st_size)))
        except PermissionError:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

        random.shuffle(entries)
        # Parent href: one level up.
        parent = "/vendor" if "/" not in clean else f"/vendor/{clean.rsplit('/', 1)[0]}/"
        return HTMLResponse(_listing_html(f"Index of /vendor/{clean}/", parent, entries))

    # --- file: return plain text ---
    if target.is_file():
        try:
            content = target.read_text(errors="replace")
        except PermissionError:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        return PlainTextResponse(content)

    # Not found.
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"'{vendor_path}' not found.",
    )
