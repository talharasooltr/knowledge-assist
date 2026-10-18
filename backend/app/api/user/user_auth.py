from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

import app.infrastructure.db.repository as db
from app.api.session_auth import (
    SessionPrincipal,
    get_session_principal,
    start_session,
    validate_login_origin,
)
from app.core.logging import log_event
from app.schemas.auth import LoginRequest

router = APIRouter()


def verify_user_credentials(request: Request) -> SessionPrincipal:
    return get_session_principal(request, "user")


@router.post("/user/auth/login")
def user_login(
    credentials: LoginRequest,
    request: Request,
    response: Response,
):
    validate_login_origin(request)
    if not db.authenticate_user(credentials.username, credentials.password):
        log_event(credentials.username, "user_auth_check", "failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
        )

    start_session(response, request, credentials.username, "user")
    log_event(credentials.username, "user_auth_check", "success")
    return {"success": True, "detail": "User authentication successful."}


@router.get("/user/auth/check")
def user_auth_check(
    principal: SessionPrincipal = Depends(verify_user_credentials),
):
    return {"success": True, "detail": "User authentication successful."}
