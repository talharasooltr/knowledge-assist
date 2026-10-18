import os
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List
from app.core.config import ADMIN_USERNAME
from app.api.admin.admin_auth import require_admin_session
from app.api.session_auth import SessionPrincipal
import app.infrastructure.db.repository as db
from app.core.logging import log_event

router = APIRouter()

class UserCreate(BaseModel):
    username: str
    password: str = Field(min_length=12, max_length=1024)

class UserOut(BaseModel):
    id: int
    username: str

@router.post("/admin/users", response_model=UserOut)
def add_user(user: UserCreate, principal: SessionPrincipal = Depends(require_admin_session)):
    if ADMIN_USERNAME and user.username == ADMIN_USERNAME:
        raise HTTPException(status_code=400, detail="Username is reserved.")
    success = db.add_user(user.username, user.password)
    if not success:
        log_event(principal.username, "admin_add_user", f"username={user.username}, failed")
        raise HTTPException(status_code=400, detail="User already exists.")
    # Fetch the user to get the id
    users = db.get_all_users()
    for u in users:
        if u['userid'] == user.username:
            log_event(principal.username, "admin_add_user", f"username={user.username}, id={u['id']}")
            return UserOut(id=u['id'], username=u['userid'])
    log_event(principal.username, "admin_add_user", f"username={user.username}, failed to fetch id")
    raise HTTPException(status_code=500, detail="User creation failed.")

@router.delete("/admin/users/{username}")
def delete_user(username: str, principal: SessionPrincipal = Depends(require_admin_session)):
    success = db.delete_user(username)
    if not success:
        log_event(principal.username, "admin_delete_user", f"username={username}, failed")
        raise HTTPException(status_code=404, detail="User not found.")
    log_event(principal.username, "admin_delete_user", f"username={username}, success")
    return {"detail": "User deleted."}

class ResetPasswordRequest(BaseModel):
    password: str = Field(min_length=12, max_length=1024)

@router.post("/admin/users/{username}/reset_password")
def reset_password(username: str, req: ResetPasswordRequest, principal: SessionPrincipal = Depends(require_admin_session)):
    success = db.update_user_password(username, req.password)
    if not success:
        log_event(principal.username, "admin_reset_password", f"username={username}, failed")
        raise HTTPException(status_code=404, detail="User not found.")
    log_event(principal.username, "admin_reset_password", f"username={username}, success")
    return {"detail": "Password reset successful."}

@router.get("/admin/users", response_model=List[UserOut])
def list_users(principal: SessionPrincipal = Depends(require_admin_session)):
    users = db.get_all_users()
    log_event(principal.username, "admin_list_users", f"count={len(users)}")
    return [UserOut(id=u['id'], username=u['userid']) for u in users]
