import unittest
from unittest.mock import ANY, patch

from fastapi.testclient import TestClient

from app.api.auth_dependencies import get_credential_authenticator
from app.application.authentication import (
    AuthenticatedIdentity,
    AuthenticationRole,
    AuthenticationConfigurationError,
)
from app.infrastructure.auth.credential_authenticator import LocalCredentialAuthenticator
from app.main import app


class LocalCredentialAuthenticatorTests(unittest.TestCase):
    def setUp(self):
        self.authenticator = LocalCredentialAuthenticator()

    @patch("app.infrastructure.auth.credential_authenticator.authenticate_user")
    @patch("app.infrastructure.auth.credential_authenticator.ADMIN_PASSWORD", "admin-secret")
    @patch("app.infrastructure.auth.credential_authenticator.ADMIN_USERNAME", "admin")
    def test_authenticates_configured_admin_without_client_role(self, authenticate_user):
        identity = self.authenticator.authenticate("admin", "admin-secret")

        self.assertEqual(identity, AuthenticatedIdentity(username="admin", role="admin"))
        authenticate_user.assert_not_called()

    @patch("app.infrastructure.auth.credential_authenticator.authenticate_user", return_value=True)
    @patch("app.infrastructure.auth.credential_authenticator.ADMIN_PASSWORD", "admin-secret")
    @patch("app.infrastructure.auth.credential_authenticator.ADMIN_USERNAME", "admin")
    def test_authenticates_regular_user_from_database(self, _authenticate_user):
        identity = self.authenticator.authenticate("member", "member-secret")

        self.assertEqual(identity, AuthenticatedIdentity(username="member", role="user"))

    @patch("app.infrastructure.auth.credential_authenticator.authenticate_user", return_value=True)
    @patch("app.infrastructure.auth.credential_authenticator.ADMIN_PASSWORD", "admin-secret")
    @patch("app.infrastructure.auth.credential_authenticator.ADMIN_USERNAME", "admin")
    def test_does_not_fall_back_to_member_for_reserved_admin_username(self, _authenticate_user):
        identity = self.authenticator.authenticate("admin", "not-admin-secret")

        self.assertIsNone(identity)

    @patch("app.infrastructure.auth.credential_authenticator.burn_password_check")
    @patch("app.infrastructure.auth.credential_authenticator.ADMIN_PASSWORD", "")
    @patch("app.infrastructure.auth.credential_authenticator.ADMIN_USERNAME", "admin")
    def test_fails_closed_if_configured_admin_has_no_password(self, burn_password_check):
        with self.assertRaises(AuthenticationConfigurationError):
            self.authenticator.authenticate("admin", "anything")
        burn_password_check.assert_called_once_with("anything")


class StubCredentialAuthenticator:
    def __init__(self):
        self.identity: AuthenticatedIdentity | None = None

    def authenticate(self, username: str, password: str) -> AuthenticatedIdentity | None:
        return self.identity


class UnifiedLoginRouteTests(unittest.TestCase):
    def setUp(self):
        self.previous_overrides = app.dependency_overrides.copy()
        self.authenticator = StubCredentialAuthenticator()
        app.dependency_overrides[get_credential_authenticator] = lambda: self.authenticator
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        app.dependency_overrides.update(self.previous_overrides)

    @patch("app.api.session_auth.start_session")
    def test_single_login_endpoint_returns_backend_resolved_role(self, start_session):
        roles: tuple[AuthenticationRole, ...] = ("user", "admin")
        for role in roles:
            self.authenticator.identity = AuthenticatedIdentity(username="account", role=role)
            response = self.client.post(
                "/auth/login",
                json={"username": "account", "password": "secret"},
                headers={"Origin": "http://localhost:4000"},
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.json(),
                {"authenticated": True, "role": role, "username": "account"},
            )
            start_session.assert_called_with(
                ANY,
                ANY,
                "account",
                role,
            )
        self.assertEqual(start_session.call_count, 2)

    def test_role_specific_login_endpoints_are_removed(self):
        self.assertEqual(
            self.client.post("/user/auth/login", json={"username": "a", "password": "b"}).status_code,
            404,
        )
        self.assertEqual(
            self.client.post("/admin/auth/login", json={"username": "a", "password": "b"}).status_code,
            404,
        )


if __name__ == "__main__":
    unittest.main()
