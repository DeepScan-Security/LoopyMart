"""
CTF-related endpoints: robots.txt (flag for robots challenge) and optional /flags/{challenge_id}.
"""

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import PlainTextResponse

from app.core.flags import get_flag

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
