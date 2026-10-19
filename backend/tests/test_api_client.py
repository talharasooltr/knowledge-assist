import unittest
from unittest.mock import Mock, patch

from clients.api_client import ApiClient


class ApiClientTests(unittest.TestCase):
    def test_state_changing_requests_include_the_session_csrf_token(self):
        client = ApiClient("http://localhost:8000/")
        client.session.cookies.set("knowledge_csrf", "csrf-token")
        response = Mock()

        with patch.object(client.session, "request", return_value=response) as request:
            result = client.post(
                "/chat/conversations/417ccbf1-6125-4de7-a77e-f4354b097e36/messages",
                json={"message": "hello"},
            )

        self.assertIs(result, response)
        request.assert_called_once_with(
            "POST",
            "http://localhost:8000/chat/conversations/417ccbf1-6125-4de7-a77e-f4354b097e36/messages",
            headers={"X-CSRF-Token": "csrf-token"},
            json={"message": "hello"},
        )

    def test_safe_requests_do_not_send_a_csrf_header(self):
        client = ApiClient("http://localhost:8000")

        with patch.object(client.session, "request", return_value=Mock()) as request:
            client.get(
                "/chat/conversations/417ccbf1-6125-4de7-a77e-f4354b097e36/messages"
            )

        request.assert_called_once_with(
            "GET",
            "http://localhost:8000/chat/conversations/417ccbf1-6125-4de7-a77e-f4354b097e36/messages",
            headers={},
        )


if __name__ == "__main__":
    unittest.main()
