import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api.dependencies import get_chat_service, get_pdf_deletion_service, get_pdf_ingestion_service
from app.api.session_auth import SessionPrincipal, require_session
from app.main import app


class StubChatService:
    def __init__(self):
        self.answered_users: list[str] = []
        self.history_users: list[str] = []

    def answer(self, user_id: str, message: str):
        self.answered_users.append(user_id)
        return SimpleNamespace(response=f"Answer to {message}", prompt="", citations=[])

    def history(self, user_id: str):
        self.history_users.append(user_id)
        return []


class StubPdfIngestionService:
    def __init__(self):
        self.calls: list[tuple[str, tuple]] = []

    def ingest_all_public_pdfs(self):
        self.calls.append(("public_all", ()))

    def ingest_user_pdfs(self, user_id: str):
        self.calls.append(("user_all", (user_id,)))

    def ingest_pdf_by_id(self, pdf_id: int):
        self.calls.append(("admin_one", (pdf_id,)))

    def ingest_user_pdf_by_id(self, pdf_id: int, user_id: str):
        self.calls.append(("user_one", (pdf_id, user_id)))


class StubPdfDeletionService:
    def __init__(self):
        self.calls: list[tuple[int, str | None]] = []

    def delete_pdf(self, pdf_id: int, owner_id: str | None = None):
        self.calls.append((pdf_id, owner_id))
        return {"filename": "document.pdf"}


class SharedApiTests(unittest.TestCase):
    def setUp(self):
        self.previous_overrides = app.dependency_overrides.copy()
        self.chat_service = StubChatService()
        app.dependency_overrides[get_chat_service] = lambda: self.chat_service
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        app.dependency_overrides.update(self.previous_overrides)

    def authenticate_as(self, username: str, role: str) -> None:
        app.dependency_overrides[require_session] = lambda: SessionPrincipal(
            username=username,
            role=role,
        )

    def test_same_chat_routes_scope_to_the_authenticated_account(self):
        for username, role in (("member", "user"), ("administrator", "admin")):
            with self.subTest(role=role):
                self.authenticate_as(username, role)
                history_response = self.client.get("/chat/history")
                chat_response = self.client.post("/chat", json={"message": "hello"})

                self.assertEqual(history_response.status_code, 200)
                self.assertEqual(history_response.json()["user_id"], username)
                self.assertEqual(chat_response.status_code, 200)
                self.assertIn(username, self.chat_service.history_users)
                self.assertIn(username, self.chat_service.answered_users)

    def test_pdf_listing_is_scoped_by_role_on_the_shared_route(self):
        with (
            patch("app.api.shared.documents.get_all_pdfs", return_value=[{"id": 1}]) as get_all,
            patch(
                "app.api.shared.documents.get_pdfs_by_user",
                return_value=[{"id": 2}],
            ) as get_user,
        ):
            self.authenticate_as("member", "user")
            member_response = self.client.get("/pdf")
            self.authenticate_as("administrator", "admin")
            admin_response = self.client.get("/pdf")

        self.assertEqual(member_response.json(), {"pdfs": [{"id": 2}]})
        self.assertEqual(admin_response.json(), {"pdfs": [{"id": 1}]})
        get_user.assert_called_once_with("member")
        get_all.assert_called_once_with()

    def test_shared_vector_source_listing_filters_private_sources_for_members(self):
        sources = [
            {"source": "member.pdf", "ingested_by": "member"},
            {"source": "public.pdf", "ingested_by": "public"},
            {"source": "other.pdf", "ingested_by": "other"},
        ]
        with patch(
            "app.api.shared.vectordb.pdf_vector_store.get_pdf_sources",
            return_value=sources,
        ):
            self.authenticate_as("member", "user")
            member_response = self.client.get("/vectordb/pdf")
            self.authenticate_as("administrator", "admin")
            admin_response = self.client.get("/vectordb/pdf")

        self.assertEqual(len(member_response.json()["sources"]), 2)
        self.assertEqual(len(admin_response.json()["sources"]), 3)

    def test_ingestion_uses_the_same_routes_with_role_scoped_service_calls(self):
        ingestion_service = StubPdfIngestionService()
        app.dependency_overrides[get_pdf_ingestion_service] = lambda: ingestion_service

        self.authenticate_as("member", "user")
        member_all = self.client.post("/vectordb/ingest/all")
        member_one = self.client.post("/vectordb/ingest/pdf/12")
        self.authenticate_as("administrator", "admin")
        admin_all = self.client.post("/vectordb/ingest/all")
        admin_one = self.client.post("/vectordb/ingest/pdf/34")

        self.assertEqual(
            [member_all.status_code, member_one.status_code, admin_all.status_code, admin_one.status_code],
            [200, 200, 200, 200],
        )
        self.assertEqual(
            ingestion_service.calls,
            [
                ("user_all", ("member",)),
                ("user_one", (12, "member")),
                ("public_all", ()),
                ("admin_one", (34,)),
            ],
        )

    def test_pdf_deletion_restricts_members_to_their_own_documents(self):
        deletion_service = StubPdfDeletionService()
        app.dependency_overrides[get_pdf_deletion_service] = lambda: deletion_service

        self.authenticate_as("member", "user")
        member_response = self.client.delete("/pdf/12")
        self.authenticate_as("administrator", "admin")
        admin_response = self.client.delete("/pdf/34")

        self.assertEqual(member_response.status_code, 200)
        self.assertEqual(admin_response.status_code, 200)
        self.assertEqual(deletion_service.calls, [(12, "member"), (34, None)])

    def test_other_users_history_remains_admin_only(self):
        response = self.client.get("/admin/chat/history/member")

        self.assertEqual(response.status_code, 401)

    def test_duplicate_role_specific_shared_routes_are_removed(self):
        registered_paths = {
            route.path
            for route in app.routes
            if hasattr(route, "path")
        }
        for old_path in (
            "/user/chat",
            "/admin/chat",
            "/user/chat/history",
            "/user/pdf",
            "/admin/pdf",
            "/user/vectordb/ingest/all",
            "/admin/vectordb/ingest/all",
        ):
            self.assertNotIn(old_path, registered_paths)


if __name__ == "__main__":
    unittest.main()
