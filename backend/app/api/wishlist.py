"""
Wishlist API routes.

Wishlists are stored in MongoDB.  Each user can create multiple named wishlists
and add products to them.

CTF Challenge – SSTI (Server-Side Template Injection)
======================================================
POST /wishlist/{wishlist_id}/share-preview accepts a ``share_template`` string
that is **rendered server-side via Jinja2 without sanitisation**.  The template
context contains:

    wishlist   – the wishlist document (name, items …)
    flag       – the value of the ``wishlist_ssti`` challenge flag

A player can exfiltrate the flag by submitting:

    {{ flag }}

or probe the server further with:

    {{ ''.__class__.__mro__[1].__subclasses__() }}
"""

import jinja2
from types import SimpleNamespace
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse

from app.api.deps import get_current_user
from app.core.flags import get_flag
from app.db.products_mongo import product_get
from app.db.wishlist_mongo import (
    wishlist_add_item,
    wishlist_create,
    wishlist_delete,
    wishlist_get_all_by_user,
    wishlist_get_by_id,
    wishlist_product_in_user_wishlists,
    wishlist_remove_item,
    wishlist_rename,
)
from app.models.user import User
from app.schemas.wishlist import (
    SharePreviewRequest,
    WishlistCreate,
    WishlistItemAdd,
    WishlistItemResponse,
    WishlistRename,
    WishlistResponse,
)

router = APIRouter(prefix="/wishlist", tags=["wishlist"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _doc_to_response(doc: dict, populate_items: bool = False) -> WishlistResponse:
    """Convert a MongoDB wishlist document to the API response schema."""
    raw_items: list[dict] = doc.get("items") or []
    items: list[WishlistItemResponse] = []
    if populate_items:
        for entry in raw_items:
            product = await product_get(entry["product_id"])
            if product:
                items.append(
                    WishlistItemResponse(
                        product_id=entry["product_id"],
                        product_name=product["name"],
                        product_price=product["price"],
                        product_image_url=product.get("image_url"),
                        added_at=entry.get("added_at"),
                    )
                )
            else:
                items.append(
                    WishlistItemResponse(
                        product_id=entry["product_id"],
                        product_name="(Unavailable)",
                        product_price=0.0,
                        product_image_url=None,
                        added_at=entry.get("added_at"),
                    )
                )
    return WishlistResponse(
        id=doc["id"],
        name=doc["name"],
        item_count=len(raw_items),
        items=items,
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),
    )


# ---------------------------------------------------------------------------
# Wishlist CRUD
# ---------------------------------------------------------------------------


@router.get("", response_model=list[WishlistResponse])
async def list_wishlists(
    current_user: User = Depends(get_current_user),
) -> list[WishlistResponse]:
    """Return all wishlists belonging to the current user (no product details)."""
    docs = await wishlist_get_all_by_user(current_user.id)
    return [await _doc_to_response(d, populate_items=False) for d in docs]


@router.post("", response_model=WishlistResponse, status_code=status.HTTP_201_CREATED)
async def create_wishlist(
    data: WishlistCreate,
    current_user: User = Depends(get_current_user),
) -> WishlistResponse:
    """Create a new named wishlist for the current user."""
    name = data.name.strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wishlist name cannot be empty",
        )
    doc = await wishlist_create(current_user.id, name)
    return await _doc_to_response(doc)


@router.get("/{wishlist_id}", response_model=WishlistResponse)
async def get_wishlist(
    wishlist_id: str,
    current_user: User = Depends(get_current_user),
) -> WishlistResponse:
    """Return a single wishlist with full product details."""
    doc = await wishlist_get_by_id(wishlist_id, current_user.id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist not found")
    return await _doc_to_response(doc, populate_items=True)


@router.patch("/{wishlist_id}", response_model=WishlistResponse)
async def rename_wishlist(
    wishlist_id: str,
    data: WishlistRename,
    current_user: User = Depends(get_current_user),
) -> WishlistResponse:
    """Rename a wishlist."""
    name = data.name.strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wishlist name cannot be empty",
        )
    doc = await wishlist_rename(wishlist_id, current_user.id, name)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist not found")
    return await _doc_to_response(doc)


@router.delete("/{wishlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wishlist(
    wishlist_id: str,
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a wishlist and all its items."""
    deleted = await wishlist_delete(wishlist_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist not found")


# ---------------------------------------------------------------------------
# Wishlist item management
# ---------------------------------------------------------------------------


@router.post("/{wishlist_id}/items", response_model=WishlistResponse)
async def add_item_to_wishlist(
    wishlist_id: str,
    data: WishlistItemAdd,
    current_user: User = Depends(get_current_user),
) -> WishlistResponse:
    """Add a product to a wishlist."""
    product = await product_get(data.product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    doc = await wishlist_add_item(wishlist_id, current_user.id, data.product_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist not found")
    return await _doc_to_response(doc)


@router.delete("/{wishlist_id}/items/{product_id}", response_model=WishlistResponse)
async def remove_item_from_wishlist(
    wishlist_id: str,
    product_id: str,
    current_user: User = Depends(get_current_user),
) -> WishlistResponse:
    """Remove a product from a wishlist."""
    doc = await wishlist_remove_item(wishlist_id, current_user.id, product_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist not found")
    return await _doc_to_response(doc)


@router.get("/check/{product_id}", response_model=list[str])
async def check_product_in_wishlists(
    product_id: str,
    current_user: User = Depends(get_current_user),
) -> list[str]:
    """Return wishlist IDs that contain the given product."""
    return await wishlist_product_in_user_wishlists(current_user.id, product_id)


# ---------------------------------------------------------------------------
# CTF Challenge: SSTI (Server-Side Template Injection)
# ---------------------------------------------------------------------------


@router.post("/{wishlist_id}/share-preview", response_class=HTMLResponse)
async def share_preview(
    wishlist_id: str,
    data: SharePreviewRequest,
    current_user: User = Depends(get_current_user),
) -> HTMLResponse:
    """Generate a shareable HTML preview for a wishlist.

    The `share_template` field is rendered via Jinja2.  You can customise the
    look & feel of your share card by using template variables:

        {{ wishlist.name }}   – wishlist name
        {{ wishlist.items }}  – list of items in the wishlist

    ⚠️  CTF Challenge – try to extract the hidden ``{{ flag }}`` value!
    """
    doc = await wishlist_get_by_id(wishlist_id, current_user.id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist not found")

    # Load product details for template context
    # Each item is a SimpleNamespace so {{ item.name }} / {{ item.price }} work
    # without colliding with dict built-ins (e.g. dict.items()).
    populated_items = []
    for entry in doc.get("items") or []:
        product = await product_get(entry["product_id"])
        populated_items.append(
            SimpleNamespace(
                product_id=entry["product_id"],
                name=product["name"] if product else "(Unavailable)",
                price=product["price"] if product else 0,
            )
        )

    # Wrap in SimpleNamespace objects so Jinja2 attribute access (wishlist.items,
    # user.name) never hits Python built-in dict methods like dict.items().
    wishlist_ns = SimpleNamespace(
        id=doc["id"],
        name=doc["name"],
        item_count=len(populated_items),
        items=populated_items,
    )
    user_ns = SimpleNamespace(
        name=current_user.full_name or current_user.email,
    )

    template_context = {
        "wishlist": wishlist_ns,
        "user":     user_ns,
        # ⚠️  CTF: the flag is injected into the template context
        "flag":     get_flag("wishlist_ssti") or "",
    }

    # ⚠️  INTENTIONALLY VULNERABLE: user-controlled template rendered unsafely
    try:
        rendered = jinja2.Template(data.share_template).render(**template_context)
    except Exception as exc:
        rendered = f"<pre>Template error: {exc}</pre>"

    # ⚠️  SECOND-ORDER SSTI: the wishlist *name* is also rendered as a Jinja2
    # template.  Store a payload via PATCH /wishlist/{id} {"name":"{{flag}}"},
    # then trigger it by requesting a share-preview on that wishlist.
    try:
        rendered_name = jinja2.Template(wishlist_ns.name).render(**template_context)
    except Exception:
        rendered_name = wishlist_ns.name

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{rendered_name} – LoopyMart Wishlist</title>
  <style>
    body {{ font-family: sans-serif; background: #f5f5f5; padding: 2rem; }}
    .card {{ background: #fff; border-radius: 8px; padding: 1.5rem; max-width: 640px;
              margin: auto; box-shadow: 0 2px 8px rgba(0,0,0,.1); }}
    h1 {{ color: #2874f0; margin-top: 0; }}
  </style>
</head>
<body>
  <div class="card">
    {rendered}
  </div>
</body>
</html>"""
    return HTMLResponse(content=html)
