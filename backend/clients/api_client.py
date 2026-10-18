from typing import Any

import requests


class ApiClient:
    _UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.username = ""

    def login(self, username: str, password: str) -> requests.Response:
        response = self.session.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password},
        )
        if response.ok:
            self.username = username
        return response

    def request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        headers = dict(kwargs.pop("headers", {}))
        if method.upper() in self._UNSAFE_METHODS:
            csrf_token = self.session.cookies.get("knowledge_csrf")
            if csrf_token:
                headers.setdefault("X-CSRF-Token", csrf_token)
        return self.session.request(
            method,
            f"{self.base_url}/{path.lstrip('/')}",
            headers=headers,
            **kwargs,
        )

    def get(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("POST", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("DELETE", path, **kwargs)
