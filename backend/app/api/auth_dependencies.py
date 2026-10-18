from app.application.authentication import CredentialAuthenticator
from app.infrastructure.auth.credential_authenticator import LocalCredentialAuthenticator


def get_credential_authenticator() -> CredentialAuthenticator:
    return LocalCredentialAuthenticator()
