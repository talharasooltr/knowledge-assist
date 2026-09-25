import asyncio

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasicCredentials
from app.api.admin.admin_auth import verify_admin_credentials
from app.api.dependencies import get_chat_service
from app.application.chat_service import ChatService
from app.infrastructure.retrieval.chat_memory import get_all_history
from app.core.logging import log_event
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()

@router.post("/admin/chat", response_model=ChatResponse)
async def admin_chat(
    req: ChatRequest,
    credentials: HTTPBasicCredentials = Depends(verify_admin_credentials),
    service: ChatService = Depends(get_chat_service),
):
    result = await asyncio.to_thread(service.answer, credentials.username, req.message)
    log_event(credentials.username, "admin_chat", f"message={req.message}")
    return ChatResponse(response=result.response, prompt=result.prompt)


@router.get("/admin/chat/history/{user_id}")
def get_chat_history(user_id: str, credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    try:
        history = get_all_history(user_id)
        log_event(credentials.username, "admin_get_chat_history", f"user_id={user_id}, count={len(history)}")
        return {"user_id": user_id, "history": history}
    except Exception as e:
        log_event(credentials.username, "admin_get_chat_history_failed", f"user_id={user_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
