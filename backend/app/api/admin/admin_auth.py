import hmac
import os

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.api.session_auth import (
    SessionPrincipal,
    get_session_principal,
    start_session,
    validate_login_origin,
)
from app.core.logging import log_event
from app.schemas.auth import LoginRequest

router = APIRouter()


def verify_admin_credentials(request: Request) -> SessionPrincipal:
    return get_session_principal(request, "admin")


@router.post("/admin/auth/login")
def admin_login(
    credentials: LoginRequest,
    request: Request,
    response: Response,
):
    validate_login_origin(request)
    correct_username = os.environ.get("ADMIN_USERNAME")
    correct_password = os.environ.get("ADMIN_PASSWORD")
    if not correct_username or not correct_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Administrator credentials are not configured.",
        )

    username_matches = hmac.compare_digest(credentials.username, correct_username)
    password_matches = hmac.compare_digest(credentials.password, correct_password)
    if not (username_matches and password_matches):
        log_event(credentials.username, "admin_auth_check", "failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect admin username or password.",
        )

    start_session(response, request, credentials.username, "admin")
    log_event(credentials.username, "admin_auth_check", "success")
    return {"detail": "Admin authentication successful."}


@router.get("/admin/auth/check")
def admin_auth_check(
    principal: SessionPrincipal = Depends(verify_admin_credentials),
):
    return {"detail": "Admin authentication successful."}
