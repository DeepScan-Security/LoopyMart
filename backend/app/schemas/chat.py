"""Chat schemas for API request/response validation."""

from pydantic import BaseModel


class ChatMessageRequest(BaseModel):
    """Schema for sending a chat message."""
    message: str


class ChatMessageResponse(BaseModel):
    """Schema for chat message response."""
    id: str
    user_id: int
    message: str
    response: str
    is_user: bool
    created_at: str


class ChatHistoryResponse(BaseModel):
    """Schema for chat history response."""
    messages: list[dict]
