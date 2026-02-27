"""
CTF-related endpoints: robots.txt (flag for robots challenge) and optional /flags/{challenge_id}.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse

from app.api.deps import get_current_user, require_admin
from app.core.flags import get_flag
from app.models.user import User

router = APIRouter(tags=["ctf"])


@router.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt() -> str:
    """
    Serve robots.txt with the CTF flag for the 'robots' challenge.
    If no flag is configured, the response does not include a flag line.
    """
    lines = [
        "User-agent: *",
        "Disallow: /admin",
    ]
    flag = get_flag("robots")
    if flag:
        lines.append(f"# flag: {flag}")
    return "\n".join(lines) + "\n"


@router.get("/flag.txt", response_class=PlainTextResponse)
def flag_txt(request: Request) -> str:
    """
    Internal-only resource — returns the SSRF invoice CTF flag.

    Accessible ONLY from loopback (127.0.0.1 / ::1).  Every external caller
    receives HTTP 403, making this unreachable directly from a browser.

    Intended SSRF exfiltration target for the invoice challenge.
    Put the following tag in any address field at checkout, then download the
    PDF invoice to see the flag rendered inline in the Shipping Address block:

        <iframe src="http://127.0.0.1:8001/flag.txt" width="500" height="500"></iframe>

    [INTENTIONALLY VULNERABLE – CTF challenge sink]
    """
    host = request.client.host if request.client else ""
    if host not in ("127.0.0.1", "::1", "localhost"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return (get_flag("ssrf_invoice") or "flag not configured") + "\n"


@router.get("/flags/{challenge_id}", response_class=PlainTextResponse)
def get_challenge_flag(challenge_id: str) -> str:
    """Return the flag for the given challenge_id as plain text."""
    flag = get_flag(challenge_id)
    if flag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found or flag not configured",
        )
    return flag


@router.post("/ctf/mock-flag-cookie")
async def mock_flag_cookie(
    current_user: User = Depends(require_admin),
) -> JSONResponse:
    """
    [CTF Challenge: Puppeteer Cookie Exfiltration]

    Admin-only endpoint that sets a `mock_flag` cookie in the HTTP response.

    The cookie is JS-readable (no HttpOnly) so Puppeteer can extract it via
    `document.cookie` after the browser navigates to any same-origin page.

    Intended exploitation flow (see solutions/puppeteer-mock-cookie/):
      1. Obtain admin credentials or admin JWT via prior recon.
      2. Use Puppeteer to log in and call this endpoint with the bearer token.
      3. Read `document.cookie` — the flag value is the `mock_flag` cookie.

    This endpoint returns 403 for non-admin callers.

    CWE-315  Cleartext Storage of Sensitive Information in a Cookie
    CWE-614  Sensitive Cookie in HTTPS Session Without 'Secure' Attribute
    """
    flag = get_flag("puppeteer_mock_cookie")
    if not flag:
        flag = "CTF{flag_not_configured}"

    response = JSONResponse(
        content={
            "message": "Admin access confirmed. Flag set as a browser cookie.",
            "hint": "Check your cookies for `mock_flag`.",
            "flag": flag,           # Also returned in JSON for the Python solve path
        }
    )
    response.set_cookie(
        key="mock_flag",
        value=flag,
        max_age=3600,
        path="/",
        samesite="lax",
        secure=False,   # deliberately insecure — CTF vulnerability demo
        httponly=False, # deliberately JS-readable — Puppeteer can read via document.cookie
    )
    return response
