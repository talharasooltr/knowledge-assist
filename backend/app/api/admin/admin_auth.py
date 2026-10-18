from fastapi import Request

from app.api.session_auth import (
    SessionPrincipal,
    get_session_principal,
)

def require_admin_session(request: Request) -> SessionPrincipal:
    return get_session_principal(request, "admin")
