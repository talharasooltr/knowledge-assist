import unittest
from unittest.mock import Mock, patch

from clients.api_client import ApiClient


class ApiClientTests(unittest.TestCase):
    def test_state_changing_requests_include_the_session_csrf_token(self):
        client = ApiClient("http://localhost:8000/")
        client.session.cookies.set("knowledge_csrf", "csrf-token")
        response = Mock()

        with patch.object(client.session, "request", return_value=response) as request:
            result = client.post("/chat", json={"message": "hello"})

        self.assertIs(result, response)
        request.assert_called_once_with(
            "POST",
            "http://localhost:8000/chat",
            headers={"X-CSRF-Token": "csrf-token"},
            json={"message": "hello"},
        )

    def test_safe_requests_do_not_send_a_csrf_header(self):
        client = ApiClient("http://localhost:8000")

        with patch.object(client.session, "request", return_value=Mock()) as request:
            client.get("/chat/history")

        request.assert_called_once_with(
            "GET",
            "http://localhost:8000/chat/history",
            headers={},
        )


if __name__ == "__main__":
    unittest.main()
