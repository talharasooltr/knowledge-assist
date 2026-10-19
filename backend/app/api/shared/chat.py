import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.dependencies import get_chat_service
from app.api.session_auth import SessionPrincipal, require_session
from app.application.chat_service import ChatService, ConversationNotFoundError
from app.core.logging import log_event
from app.schemas.chat import (
    ChatConversationHistoryResponse,
    ChatConversationListResponse,
    ChatConversationSummary,
    ChatRequest,
    ChatResponse,
)

router = APIRouter()


@router.get("/chat/conversations", response_model=ChatConversationListResponse)
def list_my_conversations(
    principal: SessionPrincipal = Depends(require_session),
    service: ChatService = Depends(get_chat_service),
):
    conversations = service.conversations(principal.username)
    return {"conversations": conversations}


@router.post(
    "/chat/conversations",
    response_model=ChatConversationSummary,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    principal: SessionPrincipal = Depends(require_session),
    service: ChatService = Depends(get_chat_service),
):
    conversation = service.create(principal.username)
    log_event(principal.username, "create_chat_conversation", f"conversation_id={conversation['id']}")
    return conversation


@router.get(
    "/chat/conversations/{conversation_id}/messages",
    response_model=ChatConversationHistoryResponse,
)
def get_conversation_history(
    conversation_id: UUID,
    principal: SessionPrincipal = Depends(require_session),
    service: ChatService = Depends(get_chat_service),
):
    try:
        history = service.history(principal.username, str(conversation_id))
    except ConversationNotFoundError as error:
        raise HTTPException(status_code=404, detail="Conversation not found.") from error
    return {"conversation_id": conversation_id, "history": history}


@router.post(
    "/chat/conversations/{conversation_id}/messages",
    response_model=ChatResponse,
)
async def send_message(
    conversation_id: UUID,
    req: ChatRequest,
    principal: SessionPrincipal = Depends(require_session),
    service: ChatService = Depends(get_chat_service),
):
    try:
        result = await asyncio.to_thread(
            service.answer,
            principal.username,
            str(conversation_id),
            req.message,
        )
    except ConversationNotFoundError as error:
        raise HTTPException(status_code=404, detail="Conversation not found.") from error
    log_event(
        principal.username,
        "chat_message",
        f"conversation_id={conversation_id}",
    )
    return ChatResponse(response=result.response, prompt=result.prompt, citations=result.citations)


@router.delete("/chat/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: UUID,
    principal: SessionPrincipal = Depends(require_session),
    service: ChatService = Depends(get_chat_service),
):
    try:
        service.delete(principal.username, str(conversation_id))
    except ConversationNotFoundError as error:
        raise HTTPException(status_code=404, detail="Conversation not found.") from error
    log_event(principal.username, "delete_chat_conversation", f"conversation_id={conversation_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
