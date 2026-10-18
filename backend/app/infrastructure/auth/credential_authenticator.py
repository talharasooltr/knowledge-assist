import hmac

from app.application.authentication import (
    AuthenticatedIdentity,
    AuthenticationConfigurationError,
    CredentialAuthenticator,
)
from app.core.config import ADMIN_PASSWORD, ADMIN_USERNAME
from app.core.passwords import burn_password_check
from app.infrastructure.db.repository import authenticate_user


class LocalCredentialAuthenticator:
    def authenticate(
        self,
        username: str,
        password: str,
    ) -> AuthenticatedIdentity | None:
        is_admin_username = bool(
            ADMIN_USERNAME and hmac.compare_digest(username, ADMIN_USERNAME)
        )
        if is_admin_username and not ADMIN_PASSWORD:
            burn_password_check(password)
            raise AuthenticationConfigurationError(
                "Administrator credentials are not configured."
            )
        if is_admin_username and hmac.compare_digest(password, ADMIN_PASSWORD):
            return AuthenticatedIdentity(username=username, role="admin")

        valid_user = authenticate_user(username, password)
        if is_admin_username:
            return None
        if valid_user:
            return AuthenticatedIdentity(username=username, role="user")
        return None
