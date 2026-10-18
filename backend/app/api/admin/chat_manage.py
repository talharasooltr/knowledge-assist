from fastapi import APIRouter, Depends, HTTPException
from app.api.admin.admin_auth import require_admin_session
from app.api.session_auth import SessionPrincipal
from app.infrastructure.retrieval.chat_memory import get_all_history
from app.core.logging import log_event
from app.schemas.chat import ChatHistoryResponse

router = APIRouter()

@router.get("/admin/chat/history/{user_id}", response_model=ChatHistoryResponse)
def get_chat_history(user_id: str, principal: SessionPrincipal = Depends(require_admin_session)):
    try:
        history = get_all_history(user_id)
        log_event(principal.username, "admin_get_chat_history", f"user_id={user_id}, count={len(history)}")
        return {"user_id": user_id, "history": history}
    except Exception as e:
        log_event(principal.username, "admin_get_chat_history_failed", f"user_id={user_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
