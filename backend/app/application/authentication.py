from dataclasses import dataclass
from typing import Literal, Protocol


AuthenticationRole = Literal["user", "admin"]


@dataclass(frozen=True)
class AuthenticatedIdentity:
    username: str
    role: AuthenticationRole


class AuthenticationConfigurationError(RuntimeError):
    pass


class CredentialAuthenticator(Protocol):
    def authenticate(
        self,
        username: str,
        password: str,
    ) -> AuthenticatedIdentity | None: ...
