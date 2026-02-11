"""
CTF-related endpoints: robots.txt (flag for robots challenge) and optional /flags/{challenge_id}.
"""

from fastapi import APIRouter, HTTPException, status
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
