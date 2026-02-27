"""
Orders API routes.
Orders are stored in MongoDB with user_id referencing SQL users.
"""

import asyncio
import functools
import re
import urllib.request

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.cart_mongo import cart_clear, cart_get_by_user
from app.db.orders_mongo import order_create, order_get, order_list_by_user, order_update_status
from app.db.products_mongo import product_decrement_stock, product_get
from app.models.user import User
from app.schemas.order import (
    CreatePaymentResponse,
    OrderCreate,
    OrderItemResponse,
    OrderResponse,
    VerifyPaymentRequest,
)

router = APIRouter(prefix="/orders", tags=["orders"])


def _order_to_response(order: dict) -> OrderResponse:
    """Convert MongoDB order to response schema."""
    items = [
        OrderItemResponse(
            product_id=item["product_id"],
            product_name=item["product_name"],
            quantity=item["quantity"],
            price_at_order=item["price_at_order"],
            product_image_url=item.get("product_image_url"),
        )
        for item in order.get("items", [])
    ]
    
    # Get payment status if available
    payment_status = None
    if order.get("status") == "paid":
        payment_status = "SUCCESS"
    elif order.get("status") == "pending":
        payment_status = "PENDING"
    elif order.get("status") in ["shipped", "delivered"]:
        payment_status = "SUCCESS"
    elif order.get("status") == "cancelled":
        payment_status = "FAILED"
    
    return OrderResponse(
        id=order["id"],
        total=order["total"],
        status=order["status"],
        shipping_address=order["shipping_address"],
        items=items,
        created_at=order.get("created_at").isoformat() if order.get("created_at") else None,
        payment_status=payment_status,
    )


def _ensure_razorpay():
    """Check if Razorpay is configured."""
    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment gateway not configured",
        )


@router.post("/create-payment", response_model=CreatePaymentResponse)
async def create_payment(
    data: OrderCreate,
    current_user: User = Depends(get_current_user),
) -> CreatePaymentResponse:
    """Create order (pending) and Razorpay order; frontend opens Razorpay checkout then calls verify-payment."""
    _ensure_razorpay()
    
    cart_items = await cart_get_by_user(current_user.id)
    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty",
        )
    
    total = 0.0
    order_items: list[dict] = []
    
    for ci in cart_items:
        product = await product_get(ci["product_id"])
        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product no longer available",
            )
        if ci["quantity"] > product["stock"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for {product['name']}",
            )
        total += product["price"] * ci["quantity"]
        order_items.append({
            "product_id": ci["product_id"],
            "product_name": product["name"],
            "quantity": ci["quantity"],
            "price_at_order": product["price"],
            "product_image_url": product.get("image_url"),
        })

    # Create Razorpay order first
    amount_paise = max(settings.min_payment_amount_paise, int(round(total * 100)))
    import razorpay
    client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
    razorpay_order = client.order.create(
        data={
            "amount": amount_paise,
            "currency": "INR",
            "receipt": f"order_{current_user.id}_{len(order_items)}",
        }
    )
    razorpay_order_id = razorpay_order["id"]

    # Create order in MongoDB
    order = await order_create(
        user_id=current_user.id,
        total=total,
        shipping_address=data.shipping_address.model_dump(),
        items=order_items,
        status="pending",
        razorpay_order_id=razorpay_order_id,
    )

    return CreatePaymentResponse(
        order_id=order["id"],
        amount=total,
        amount_paise=amount_paise,
        currency="INR",
        razorpay_order_id=razorpay_order_id,
        key_id=settings.razorpay_key_id,
    )


@router.post("/verify-payment", response_model=OrderResponse)
async def verify_payment(
    data: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user),
) -> OrderResponse:
    """Verify Razorpay signature, then decrement stock, clear cart, mark order paid."""
    _ensure_razorpay()
    
    order = await order_get(data.order_id, user_id=current_user.id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order["status"] != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order already processed",
        )

    import razorpay
    client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": data.razorpay_order_id,
            "razorpay_payment_id": data.razorpay_payment_id,
            "razorpay_signature": data.razorpay_signature,
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment verification failed: {e!s}",
        )

    # Decrement stock for each item
    for item in order.get("items", []):
        await product_decrement_stock(item["product_id"], item["quantity"])
    
    # Clear cart
    await cart_clear(current_user.id)
    
    # Update order status
    updated_order = await order_update_status(
        order["id"],
        status="paid",
        razorpay_payment_id=data.razorpay_payment_id,
    )
    
    return _order_to_response(updated_order)


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreate,
    current_user: User = Depends(get_current_user),
) -> OrderResponse:
    """Create an order without payment (COD or free)."""
    cart_items = await cart_get_by_user(current_user.id)
    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty",
        )
    
    total = 0.0
    order_items: list[dict] = []
    
    for ci in cart_items:
        product = await product_get(ci["product_id"])
        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product no longer available",
            )
        if ci["quantity"] > product["stock"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for {product['name']}",
            )
        total += product["price"] * ci["quantity"]
        order_items.append({
            "product_id": ci["product_id"],
            "product_name": product["name"],
            "quantity": ci["quantity"],
            "price_at_order": product["price"],
            "product_image_url": product.get("image_url"),
        })

    # Create order in MongoDB
    order = await order_create(
        user_id=current_user.id,
        total=total,
        shipping_address=data.shipping_address.model_dump(),
        items=order_items,
        status="pending",
    )

    # Decrement stock for each item
    for item in order_items:
        await product_decrement_stock(item["product_id"], item["quantity"])
    
    # Clear cart
    await cart_clear(current_user.id)

    return _order_to_response(order)


@router.get("", response_model=list[OrderResponse])
async def list_orders(
    current_user: User = Depends(get_current_user),
) -> list[OrderResponse]:
    """List all orders for the current user."""
    orders = await order_list_by_user(current_user.id)
    return [_order_to_response(o) for o in orders]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
) -> OrderResponse:
    """Get a specific order by ID."""
    order = await order_get(order_id, user_id=current_user.id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return _order_to_response(order)


def _resolve_html_ssrf(field: str, styles) -> list:
    """
    Scan one address-field value for <img src> and <iframe src> tags and
    resolve them server-side via urllib, returning a list of reportlab flowables.

    • <img src="URL">    — attempt HTTP GET; emit a grey italic probe stamp so the
                           attacker can confirm the server-side request fired.
    • <iframe src="URL"> — fetch the URL body and render the full response text
                           inline in red monospaced type (flag exfiltration sink).

    Plain text spans between tags are emitted as normal body paragraphs.

    [INTENTIONALLY VULNERABLE – CTF challenge]
    """
    from html import escape as _esc

    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph

    body_style = ParagraphStyle(
        "_SSRFBody", parent=styles["Normal"], fontSize=9, leading=13,
    )
    probe_style = ParagraphStyle(
        "_SSRFProbe", parent=styles["Normal"],
        fontSize=8, fontName="Helvetica-Oblique",
        textColor=colors.HexColor("#9E9E9E"), leading=12,
    )
    exfil_style = ParagraphStyle(
        "_SSRFExfil", parent=styles["Normal"],
        fontSize=9, fontName="Courier",
        textColor=colors.HexColor("#B71C1C"), leading=14,
    )
    err_style = ParagraphStyle(
        "_SSRFErr", parent=styles["Normal"],
        fontSize=8, fontName="Helvetica-Oblique",
        textColor=colors.HexColor("#B71C1C"), leading=12,
    )

    combined = re.compile(
        r'(<img\b[^>]*?\bsrc=["\']([^"\']+)["\'][^>]*/?>)'
        r'|'
        r'(<iframe\b[^>]*?\bsrc=["\']([^"\']+)["\'][^>]*>.*?</iframe>)',
        re.IGNORECASE | re.DOTALL,
    )

    flowables: list = []
    last = 0

    for m in combined.finditer(field):
        prefix = field[last:m.start()]
        if prefix.strip():
            flowables.append(Paragraph(_esc(prefix).replace("\n", "<br/>"), body_style))
        last = m.end()

        if m.group(1):  # <img ...>
            url = m.group(2)
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": "LoopyMart-InvoiceBot/1.0"},
                )
                with urllib.request.urlopen(req, timeout=8) as resp:  # noqa: S310
                    size = len(resp.read())
                flowables.append(
                    Paragraph(f"[\U0001f5bc Image: {_esc(url)} \u2014 {size} bytes received]", probe_style)
                )
            except Exception as exc:  # noqa: BLE001
                flowables.append(
                    Paragraph(f"[\U0001f5bc Broken image \u2014 {_esc(str(exc)[:140])}]", probe_style)
                )

        else:  # <iframe ...>
            url = m.group(4)
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": "LoopyMart-InvoiceBot/1.0"},
                )
                with urllib.request.urlopen(req, timeout=8) as resp:  # noqa: S310
                    body_text = resp.read().decode("utf-8", errors="replace").strip()
                safe_body = _esc(body_text).replace("\n", "<br/>") or "(empty response)"
                flowables.append(Paragraph(safe_body, exfil_style))
            except Exception as exc:  # noqa: BLE001
                flowables.append(
                    Paragraph(f"[iframe fetch error: {_esc(str(exc)[:140])}]", err_style)
                )

    tail = field[last:]
    if tail.strip():
        flowables.append(Paragraph(_esc(tail).replace("\n", "<br/>"), body_style))

    return flowables


def _build_invoice_pdf(order: dict, addr: dict | str) -> bytes:
    """Build a PDF invoice using reportlab and return raw bytes."""
    from io import BytesIO

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        HRFlowable,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=15 * mm, bottomMargin=15 * mm,
    )
    styles = getSampleStyleSheet()
    page_w = A4[0] - 40 * mm
    brand_blue = colors.HexColor("#2874F0")
    light_gray = colors.HexColor("#F5F5F5")

    title_style = ParagraphStyle(
        "InvTitle", parent=styles["Normal"],
        fontSize=22, textColor=brand_blue, alignment=1, fontName="Helvetica-Bold",
    )
    sub_style = ParagraphStyle(
        "InvSub", parent=styles["Normal"],
        fontSize=11, textColor=colors.grey, alignment=1,
    )
    section_style = ParagraphStyle(
        "InvSection", parent=styles["Normal"],
        fontSize=10, textColor=brand_blue, fontName="Helvetica-Bold",
    )
    body_style = ParagraphStyle(
        "InvBody", parent=styles["Normal"], fontSize=9, leading=13,
    )
    mono_style = ParagraphStyle(
        "InvMono", parent=styles["Normal"],
        fontSize=9, fontName="Courier", leading=14,
    )
    footer_style = ParagraphStyle(
        "InvFooter", parent=styles["Normal"],
        fontSize=8, alignment=1, textColor=colors.grey,
    )

    story = []

    # Header
    story.append(Paragraph("LoopyMart", title_style))
    story.append(Paragraph("Tax Invoice / Order Receipt", sub_style))
    story.append(Spacer(1, 4 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=brand_blue))
    story.append(Spacer(1, 4 * mm))

    # Meta row
    created = order.get("created_at")
    order_date = (
        created.strftime("%d %b %Y") if hasattr(created, "strftime")
        else (str(created)[:10] if created else "N/A")
    )
    meta_table = Table(
        [
            [
                Paragraph("<b>Invoice No.</b>", body_style), Paragraph(order["id"][:8].upper(), body_style),
                Paragraph("<b>Status</b>", body_style), Paragraph(order.get("status", "").upper(), body_style),
            ],
            [
                Paragraph("<b>Order ID</b>", body_style), Paragraph(order["id"], body_style),
                Paragraph("<b>Date</b>", body_style), Paragraph(order_date, body_style),
            ],
        ],
        colWidths=[28 * mm, 62 * mm, 25 * mm, 55 * mm],
    )
    meta_table.setStyle(TableStyle([
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 5 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 4 * mm))

    # Shipping address
    # Each field is scanned for <img>/<iframe> tags by _resolve_html_ssrf.
    # Tags trigger server-side fetches — <img> confirms SSRF (probe stamp),
    # <iframe> exfiltrates the response body inline.  [INTENTIONALLY VULNERABLE]
    story.append(Paragraph("Shipping Address", section_style))
    story.append(Spacer(1, 2 * mm))
    if isinstance(addr, dict):
        addr_fields = [
            addr.get("full_name", "") + (f" \u00b7 {addr.get('phone')}" if addr.get("phone") else ""),
            addr.get("address_line1", ""),
            addr.get("address_line2", ""),
            (f"Near {addr.get('landmark')}" if addr.get("landmark") else ""),
            f"{addr.get('city', '')}, {addr.get('state', '')} \u2013 {addr.get('pincode', '')}",
            addr.get("country", "India"),
        ]
    else:
        addr_fields = [str(addr)]
    for part in addr_fields:
        if not part.strip():
            continue
        for flowable in _resolve_html_ssrf(part, styles):
            story.append(flowable)
    story.append(Spacer(1, 4 * mm))

    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 4 * mm))

    # Items table
    story.append(Paragraph("Order Items", section_style))
    story.append(Spacer(1, 2 * mm))
    col_w = [page_w * 0.5, page_w * 0.1, page_w * 0.2, page_w * 0.2]
    rows = [[
        Paragraph("<b>Product</b>", body_style), Paragraph("<b>Qty</b>", body_style),
        Paragraph("<b>Unit Price</b>", body_style), Paragraph("<b>Total</b>", body_style),
    ]]
    for item in order.get("items", []):
        lt = item["price_at_order"] * item["quantity"]
        rows.append([
            Paragraph(item.get("product_name", ""), body_style),
            Paragraph(str(item.get("quantity", "")), body_style),
            Paragraph(f"\u20b9{item['price_at_order']:,.2f}", body_style),
            Paragraph(f"\u20b9{lt:,.2f}", body_style),
        ])
    items_table = Table(rows, colWidths=col_w)
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), brand_blue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_gray]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 2 * mm))
    total_table = Table(
        [["" , "", Paragraph("<b>Grand Total</b>", body_style),
          Paragraph(f"<b>\u20b9{order['total']:,.2f}</b>", body_style)]],
        colWidths=col_w,
    )
    total_table.setStyle(TableStyle([
        ("ALIGN", (2, 0), (-1, 0), "RIGHT"),
        ("LINEABOVE", (2, 0), (-1, 0), 1, brand_blue),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(total_table)

    # Footer
    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        "Thank you for shopping with LoopyMart!  \u00b7  support@loopymart.xyz",
        footer_style,
    ))

    doc.build(story)
    return buf.getvalue()


@router.get("/{order_id}/invoice")
async def generate_invoice(
    order_id: str,
    current_user: User = Depends(get_current_user),
) -> Response:
    """
    Generate and download a PDF invoice for the order.

    The invoice is built server-side from the stored order data including all
    shipping-address fields.  Each field is scanned for HTML tags before
    being rendered into the PDF.

    .. warning::
        [INTENTIONALLY VULNERABLE – CTF challenge]
        <img src="URL"> and <iframe src="URL"> tags in any address field trigger
        server-side urllib fetches with no host or scheme allowlist.

        Two-step exploit:
          1. Probe  – put  <img src="http://127.0.0.1:8001/nonexistent">  in any
             address field.  Download the PDF; the Shipping Address section will
             show a grey broken-image stamp confirming the server-side request
             fired (blind SSRF confirmed).
          2. Exfil  – put  <iframe src="http://127.0.0.1:8001/flag.txt"
             width="500" height="500"></iframe>  in any address field.  Download
             the PDF; the full flag is rendered inline in red monospace inside
             the Shipping Address block.
    """
    order = await order_get(order_id, user_id=current_user.id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    addr = order.get("shipping_address", {})
    if isinstance(addr, str):
        addr = {"address_line1": addr}

    # Offload the synchronous PDF build (which fires urllib requests for <img>/<iframe>
    # tags) to a thread-pool executor.  Without this, urlopen blocks the async event
    # loop and uvicorn cannot serve the loopback /flag.txt request -> deadlock -> timeout.
    loop = asyncio.get_running_loop()
    pdf_bytes = await loop.run_in_executor(
        None, functools.partial(_build_invoice_pdf, order, addr)
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="invoice-{order_id[:8]}.pdf"',
        },
    )
