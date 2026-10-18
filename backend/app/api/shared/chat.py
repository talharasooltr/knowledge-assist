import asyncio

from fastapi import APIRouter, Depends

from app.api.dependencies import get_chat_service
from app.api.session_auth import SessionPrincipal, require_session
from app.application.chat_service import ChatService
from app.core.logging import log_event
from app.infrastructure.retrieval.chat_memory import clear_history_by_user, get_all_history
from app.schemas.chat import ChatHistoryResponse, ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    principal: SessionPrincipal = Depends(require_session),
    service: ChatService = Depends(get_chat_service),
):
    result = await asyncio.to_thread(service.answer, principal.username, req.message)
    log_event(principal.username, "chat", f"message={req.message}")
    return ChatResponse(response=result.response, prompt=result.prompt, citations=result.citations)


@router.get("/chat/history", response_model=ChatHistoryResponse)
async def get_my_history(
    principal: SessionPrincipal = Depends(require_session),
    service: ChatService = Depends(get_chat_service),
):
    history = await asyncio.to_thread(service.history, principal.username)
    log_event(principal.username, "get_chat_history", f"count={len(history)}")
    return {"user_id": principal.username, "history": history}


@router.delete("/chat/history")
def clear_my_history(principal: SessionPrincipal = Depends(require_session)):
    clear_history_by_user(principal.username)
    log_event(principal.username, "clear_chat_history", "chat history cleared")
    return {"detail": "Your chat history was cleared."}
