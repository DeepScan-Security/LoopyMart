"""
Support Tickets API routes.

CTF Challenge — IDOR via UUID Sandwich Attack
==============================================
**Challenge ID:** ``idor_uuid_sandwich``
**Category:**     Web / Insecure Direct Object Reference (IDOR)
**Difficulty:**   Medium

Mechanic
--------
Every ``POST /tickets`` call does the following atomically (from the
client's perspective) but in sequence on the server:

    1. Create the user's ticket  →  ticket_uuid **A** (returned to caller)
    2. Create a hidden *internal* system ticket  →  ticket_uuid **B**
       (never returned directly; contains the CTF flag)

Because all UUIDs are generated with ``uuid.uuid1()`` (RFC 4122 version 1),
they embed a monotonically-increasing 60-bit timestamp in 100 ns resolution.
UUIDs created later compare *greater*.

After two consecutive POST calls the attacker holds:

    uuid_A  (1st user ticket)
    uuid_C  (2nd user ticket, which becomes their third call)

The hidden ticket B was sandwiched between them:

    uuid_A  <  uuid_B  <  uuid_C

Vulnerable endpoint
-------------------
``GET /tickets/{ticket_uuid}`` fetches the ticket purely by UUID — **no
ownership check is performed**.  Any authenticated user can read any
ticket, including the internal one containing the flag.

Exploitation
------------
1.  ``POST /tickets``  →  record ``uuid_A``
2.  ``POST /tickets``  →  record ``uuid_C``
3.  Extract the 60-bit timestamp from both UUIDs.
4.  Enumerate every UUID with the same node + clock_seq but with a
    timestamp ``t`` where  ``uuid_A.time < t < uuid_C.time``.
5.  ``GET /tickets/{candidate}`` for each candidate until a hit with a
    ``flag`` field appears in the JSON response.

Mitigation
----------
* Add ``user_id`` to the DB query in ``ticket_get_by_uuid``.
* Return 403 (not 404) when the ticket belongs to another user to avoid
  leaking existence via timing.
"""

import asyncio

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.flags import get_flag
from app.db.tickets_mongo import ticket_create, ticket_get_by_uuid, ticket_list_by_user
from app.models.user import User
from app.schemas.ticket import TicketCreateRequest, TicketResponse

router = APIRouter(prefix="/tickets", tags=["tickets"])


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _doc_to_response(doc: dict) -> TicketResponse:
    return TicketResponse(
        ticket_uuid=doc["ticket_uuid"],
        subject=doc["subject"],
        message=doc["message"],
        created_at=doc.get("created_at"),
        flag=doc.get("flag"),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    data: TicketCreateRequest,
    current_user: User = Depends(get_current_user),
) -> TicketResponse:
    """
    Submit a new support ticket.

    **CTF mechanic:** immediately after creating the user ticket, the server
    silently creates a hidden internal ticket containing the challenge flag.
    The two UUIDs are time-ordered, so the internal UUID is always sandwiched
    between consecutive user-ticket UUIDs.
    """
    # Step 1 — Create the user's ticket.
    user_ticket = await ticket_create(
        user_id=current_user.id,
        subject=data.subject,
        message=data.message,
    )

    # Step 2 — Silently insert the internal (hidden) CTF ticket.
    #
    # A brief yield + sleep ensures the internal UUID's timestamp is strictly
    # between the user ticket UUID (just created) and the *next* user ticket
    # UUID (created by the attacker's second POST).  The sleep is long enough
    # to guarantee clock advancement but short enough that the attacker's two
    # POSTs still bracket it.
    await asyncio.sleep(0.001)  # 1 ms — deterministic sandwich gap

    flag_value = get_flag("idor_uuid_sandwich")
    await ticket_create(
        user_id=0,  # system / no real user
        subject="[INTERNAL] Automated system diagnostic report",
        message=(
            "This ticket was generated automatically by the LoopyMart "
            "monitoring service.  It is intended for internal review only "
            "and must not be shared with customers."
        ),
        is_internal=True,
        flag=flag_value,
    )

    return _doc_to_response(user_ticket)


@router.get("/mine", response_model=list[TicketResponse])
async def list_my_tickets(
    current_user: User = Depends(get_current_user),
) -> list[TicketResponse]:
    """
    Return the current user's own support tickets (ownership-scoped — safe).
    """
    docs = await ticket_list_by_user(current_user.id)
    return [_doc_to_response(d) for d in docs]


@router.get("/{ticket_uuid}", response_model=TicketResponse)
async def get_ticket(
    ticket_uuid: str,
    current_user: User = Depends(get_current_user),  # noqa: ARG001 — auth required, ownership NOT checked
) -> TicketResponse:
    """
    Fetch a support ticket by its UUID.

    ⚠️  **Intentionally vulnerable (IDOR):** the lookup is performed against
    the ``ticket_uuid`` field only — ``user_id`` is never compared.  Any
    authenticated user can retrieve any ticket, including internal ones.

    The flag appears in the ``flag`` field of the internal ticket response.
    """
    ticket = await ticket_get_by_uuid(ticket_uuid)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )
    return _doc_to_response(ticket)
