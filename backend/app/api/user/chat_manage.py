import asyncio

from fastapi import APIRouter, Depends
from fastapi.security import HTTPBasicCredentials

from app.api.dependencies import get_chat_service
from app.api.user.user_auth import verify_user_credentials
from app.core.logging import log_event
from app.application.chat_service import ChatService
from app.schemas.chat import ChatHistoryResponse, ChatRequest, ChatResponse

router = APIRouter()

@router.post("/user/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    credentials: HTTPBasicCredentials = Depends(verify_user_credentials),
    service: ChatService = Depends(get_chat_service),
):
    result = await asyncio.to_thread(service.answer, credentials.username, req.message)
    log_event(credentials.username, "user_chat", f"message={req.message}")
    return ChatResponse(response=result.response, prompt=result.prompt, citations=result.citations)

@router.get("/user/chat/history", response_model=ChatHistoryResponse)
async def get_my_history(
    credentials: HTTPBasicCredentials = Depends(verify_user_credentials),
    service: ChatService = Depends(get_chat_service),
):
    history = await asyncio.to_thread(service.history, credentials.username)
    log_event(credentials.username, "user_get_chat_history", f"count={len(history)}")
    return {"user_id": credentials.username, "history": history}
