"""Schemas for the Support Ticket IDOR challenge."""

from datetime import datetime

from pydantic import BaseModel


class TicketCreateRequest(BaseModel):
    """Payload for creating a new support ticket."""
    subject: str
    message: str


class TicketResponse(BaseModel):
    """Response schema for a support ticket.

    NOTE: When the requested ticket is the hidden internal ticket the
    ``flag`` field will be populated — this is intentional for the CTF.
    """
    ticket_uuid: str
    subject: str
    message: str
    created_at: datetime | None = None
    # Only present on the hidden system ticket — this is the CTF prize.
    flag: str | None = None
