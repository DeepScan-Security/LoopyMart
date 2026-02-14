"""
Support Chat API routes (with dummy AI responses).
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.db.chat_mongo import chat_create, chat_get_history, generate_ai_response
from app.models.user import User
from app.schemas.chat import ChatHistoryResponse, ChatMessageRequest, ChatMessageResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatMessageResponse)
async def send_chat_message(
    data: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
) -> ChatMessageResponse:
    """Send a chat message and get AI response."""
    # Generate AI response
    ai_response = generate_ai_response(data.message)
    
    # Store chat message
    chat = await chat_create(
        user_id=current_user.id,
        message=data.message,
        response=ai_response,
    )
    
    return ChatMessageResponse(
        id=chat["id"],
        user_id=chat["user_id"],
        message=chat["message"],
        response=chat["response"],
        is_user=chat["is_user"],
        created_at=chat["created_at"].isoformat(),
    )


@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    current_user: User = Depends(get_current_user),
) -> ChatHistoryResponse:
    """Get chat history for current user."""
    history = await chat_get_history(current_user.id)
    
    messages = []
    for chat in history:
        # Add user message
        messages.append({
            "id": f"{chat['id']}_user",
            "message": chat["message"],
            "is_user": True,
            "created_at": chat["created_at"].isoformat(),
        })
        # Add AI response
        messages.append({
            "id": f"{chat['id']}_ai",
            "message": chat["response"],
            "is_user": False,
            "created_at": chat["created_at"].isoformat(),
        })
    
    return ChatHistoryResponse(messages=messages)
