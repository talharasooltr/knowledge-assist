import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from fastapi import HTTPException, Response
from starlette.requests import Request

from app.api.session_auth import (
    CSRF_COOKIE_NAME,
    CSRF_HEADER_NAME,
    SESSION_COOKIE_NAME,
    SessionPrincipal,
    get_session_principal,
    set_session_cookies,
    validate_login_origin,
)
from app.infrastructure.auth.session_store import StoredSession


class SessionAuthTests(unittest.TestCase):
    def make_request(
        self,
        method: str = "GET",
        csrf_cookie: str | None = None,
        csrf_header: str | None = None,
        origin: str | None = None,
    ) -> Request:
        cookies = [f"{SESSION_COOKIE_NAME}=opaque-session"]
        if csrf_cookie is not None:
            cookies.append(f"{CSRF_COOKIE_NAME}={csrf_cookie}")
        headers = [(b"cookie", "; ".join(cookies).encode("ascii"))]
        if csrf_header is not None:
            headers.append((CSRF_HEADER_NAME.lower().encode("ascii"), csrf_header.encode("ascii")))
        if origin is not None:
            headers.append((b"origin", origin.encode("ascii")))
        return Request(
            {
                "type": "http",
                "method": method,
                "scheme": "http",
                "path": "/protected",
                "raw_path": b"/protected",
                "query_string": b"",
                "headers": headers,
                "server": ("testserver", 80),
                "client": ("testclient", 12345),
                "http_version": "1.1",
            }
        )

    def stored_session(self, role: str = "user") -> StoredSession:
        import hashlib

        return StoredSession(
            username="member",
            role=role,
            csrf_token_hash=hashlib.sha256(b"csrf-value").hexdigest(),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )

    @patch("app.api.session_auth.get_session_by_token")
    def test_authenticated_safe_request_needs_no_csrf_token(self, get_session):
        get_session.return_value = self.stored_session()

        principal = get_session_principal(self.make_request(), "user")

        self.assertEqual(principal, SessionPrincipal(username="member", role="user"))

    @patch("app.api.session_auth.get_session_by_token")
    def test_authenticated_mutation_requires_bound_csrf_token(self, get_session):
        get_session.return_value = self.stored_session()
        request = self.make_request("POST", csrf_cookie="csrf-value", csrf_header="csrf-value")

        principal = get_session_principal(request, "user")

        self.assertEqual(principal.username, "member")

    @patch("app.api.session_auth.get_session_by_token")
    def test_rejects_invalid_csrf_token(self, get_session):
        get_session.return_value = self.stored_session()
        request = self.make_request("DELETE", csrf_cookie="wrong", csrf_header="wrong")

        with self.assertRaises(HTTPException) as raised:
            get_session_principal(request, "user")

        self.assertEqual(raised.exception.status_code, 403)

    @patch("app.api.session_auth.get_session_by_token")
    def test_rejects_session_for_the_wrong_role(self, get_session):
        get_session.return_value = self.stored_session(role="admin")

        with self.assertRaises(HTTPException) as raised:
            get_session_principal(self.make_request(), "user")

        self.assertEqual(raised.exception.status_code, 403)

    def test_session_cookie_is_http_only_and_can_be_secure(self):
        response = Response()
        with patch("app.api.session_auth.SESSION_COOKIE_SECURE", True):
            set_session_cookies(response, "session-value", "csrf-value")
        cookies = [
            value.decode("latin-1")
            for name, value in response.raw_headers
            if name == b"set-cookie"
        ]

        self.assertEqual(len(cookies), 2)
        self.assertIn("knowledge_session=session-value", cookies[0])
        self.assertIn("httponly", cookies[0].lower())
        self.assertIn("secure", cookies[0].lower())
        self.assertNotIn("httponly", cookies[1].lower())
        self.assertIn("samesite=lax", cookies[1].lower())

    def test_rejects_untrusted_login_origin(self):
        request = self.make_request(method="POST", origin="https://attacker.example")

        with self.assertRaises(HTTPException) as raised:
            validate_login_origin(request)

        self.assertEqual(raised.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
