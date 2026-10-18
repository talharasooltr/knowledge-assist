from dataclasses import dataclass
import hashlib
import hmac
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.api.auth_dependencies import get_credential_authenticator
from app.application.authentication import (
    AuthenticationConfigurationError,
    CredentialAuthenticator,
)
from app.core.config import (
    CORS_ALLOWED_ORIGINS,
    SESSION_COOKIE_SECURE,
    SESSION_TTL_HOURS,
)
from app.infrastructure.auth.session_store import (
    StoredSession,
    create_session,
    get_session_by_token,
    revoke_session,
)
from app.core.logging import log_event
from app.schemas.auth import LoginRequest, LoginResponse

SESSION_COOKIE_NAME = "knowledge_session"
CSRF_COOKIE_NAME = "knowledge_csrf"
CSRF_HEADER_NAME = "X-CSRF-Token"
_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

router = APIRouter()


@dataclass(frozen=True)
class SessionPrincipal:
    username: str
    role: Literal["user", "admin"]


def validate_login_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin is not None and origin.rstrip("/") not in CORS_ALLOWED_ORIGINS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requests from this origin are not allowed.",
        )


def _principal_from_session(
    request: Request,
    stored: StoredSession,
    expected_role: Literal["user", "admin"] | None,
) -> SessionPrincipal:
    if expected_role is not None and stored.role != expected_role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")

    if request.method in _UNSAFE_METHODS:
        csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
        csrf_header = request.headers.get(CSRF_HEADER_NAME)
        if not csrf_cookie or not csrf_header:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token required.")
        if not hmac.compare_digest(csrf_cookie, csrf_header) or not hmac.compare_digest(
            stored.csrf_token_hash,
            hashlib.sha256(csrf_header.encode("utf-8")).hexdigest(),
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token.")

    return SessionPrincipal(username=stored.username, role=stored.role)


def get_session_principal(
    request: Request,
    expected_role: Literal["user", "admin"] | None = None,
) -> SessionPrincipal:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    stored = get_session_by_token(token)
    if stored is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or invalid.")
    return _principal_from_session(request, stored, expected_role)


def require_session(request: Request) -> SessionPrincipal:
    return get_session_principal(request)


def get_optional_session_principal(request: Request) -> SessionPrincipal | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    stored = get_session_by_token(token)
    if stored is None:
        return None
    return _principal_from_session(request, stored, None)


def set_session_cookies(
    response: Response,
    token: str,
    csrf_token: str,
) -> None:
    max_age = SESSION_TTL_HOURS * 60 * 60
    cookie_options = {
        "max_age": max_age,
        "path": "/",
        "secure": SESSION_COOKIE_SECURE,
        "samesite": "lax",
    }
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        httponly=True,
        **cookie_options,
    )
    response.set_cookie(
        CSRF_COOKIE_NAME,
        csrf_token,
        httponly=False,
        **cookie_options,
    )


def clear_session_cookies(response: Response) -> None:
    response.delete_cookie(
        SESSION_COOKIE_NAME,
        path="/",
        secure=SESSION_COOKIE_SECURE,
        httponly=True,
        samesite="lax",
    )
    response.delete_cookie(
        CSRF_COOKIE_NAME,
        path="/",
        secure=SESSION_COOKIE_SECURE,
        httponly=False,
        samesite="lax",
    )


def start_session(
    response: Response,
    request: Request,
    username: str,
    role: Literal["user", "admin"],
) -> None:
    previous_token = request.cookies.get(SESSION_COOKIE_NAME)
    if previous_token:
        revoke_session(previous_token)
    token, csrf_token, _ = create_session(username, role)
    set_session_cookies(response, token, csrf_token)


@router.post("/auth/login", response_model=LoginResponse)
def login(
    credentials: LoginRequest,
    request: Request,
    response: Response,
    authenticator: CredentialAuthenticator = Depends(get_credential_authenticator),
):
    validate_login_origin(request)
    try:
        identity = authenticator.authenticate(credentials.username, credentials.password)
    except AuthenticationConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error

    if identity is None:
        log_event(credentials.username, "auth_login", "failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
        )

    start_session(response, request, identity.username, identity.role)
    log_event(identity.username, "auth_login", f"success role={identity.role}")
    return LoginResponse(
        authenticated=True,
        role=identity.role,
        username=identity.username,
    )


@router.get("/auth/session")
def current_session(request: Request, response: Response):
    principal = get_optional_session_principal(request)
    if principal is None:
        clear_session_cookies(response)
        return {"authenticated": False}
    return {
        "authenticated": True,
        "role": principal.role,
        "username": principal.username,
    }


@router.post("/auth/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        get_optional_session_principal(request)
        revoke_session(token)
    clear_session_cookies(response)
    return {"success": True}
