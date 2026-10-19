import unittest
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID

from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_chat_service,
    get_document_ingestion_service,
    get_pdf_deletion_service,
)
from app.api.session_auth import SessionPrincipal, require_session
from app.application.chat_service import ConversationNotFoundError
from app.main import app

CONVERSATION_ID = UUID("417ccbf1-6125-4de7-a77e-f4354b097e36")


class StubChatService:
    def __init__(self):
        self.answered_conversations: list[tuple[str, str]] = []
        self.history_conversations: list[tuple[str, str]] = []
        self.created_conversations: list[tuple[str, dict]] = []

    def answer(self, user_id: str, conversation_id: str, message: str):
        if (user_id, conversation_id) not in {
            (owner, conversation["id"])
            for owner, conversation in self.created_conversations
        }:
            raise ConversationNotFoundError(conversation_id)
        self.answered_conversations.append((user_id, conversation_id))
        return SimpleNamespace(response=f"Answer to {message}", prompt="", citations=[])

    def history(self, user_id: str, conversation_id: str):
        if (user_id, conversation_id) not in {
            (owner, conversation["id"])
            for owner, conversation in self.created_conversations
        }:
            raise ConversationNotFoundError(conversation_id)
        self.history_conversations.append((user_id, conversation_id))
        return []

    def create(self, user_id: str):
        conversation = {
            "id": str(CONVERSATION_ID),
            "title": "New chat",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        self.created_conversations.append((user_id, conversation))
        return conversation

    def delete(self, user_id: str, conversation_id: str):
        if (user_id, conversation_id) not in {
            (owner, conversation["id"])
            for owner, conversation in self.created_conversations
        }:
            raise ConversationNotFoundError(conversation_id)
        self.created_conversations = [
            (owner, conversation)
            for owner, conversation in self.created_conversations
            if owner != user_id or conversation["id"] != conversation_id
        ]

    def conversations(self, user_id: str):
        return [
            conversation
            for owner, conversation in self.created_conversations
            if owner == user_id
        ]


class StubDocumentIngestionService:
    def __init__(self):
        self.calls: list[tuple[str, tuple]] = []

    def ingest_all_public_documents(self):
        self.calls.append(("public_all", ()))

    def ingest_user_documents(self, user_id: str):
        self.calls.append(("user_all", (user_id,)))

    def ingest_document_by_id(self, pdf_id: int):
        self.calls.append(("admin_one", (pdf_id,)))

    def ingest_user_document_by_id(self, pdf_id: int, user_id: str):
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

    def test_conversations_and_messages_are_scoped_to_the_authenticated_account(self):
        for username, role in (("member", "user"), ("administrator", "admin")):
            with self.subTest(role=role):
                self.authenticate_as(username, role)
                create_response = self.client.post("/chat/conversations")
                conversation_id = create_response.json()["id"]
                history_response = self.client.get(
                    f"/chat/conversations/{conversation_id}/messages"
                )
                chat_response = self.client.post(
                    f"/chat/conversations/{conversation_id}/messages",
                    json={"message": "hello"},
                )

                self.assertEqual(create_response.status_code, 201)
                self.assertEqual(history_response.status_code, 200)
                self.assertEqual(history_response.json()["conversation_id"], conversation_id)
                self.assertEqual(chat_response.status_code, 200)
                self.assertIn((username, conversation_id), self.chat_service.history_conversations)
                self.assertIn((username, conversation_id), self.chat_service.answered_conversations)

    def test_conversation_list_and_deletion_are_owner_scoped(self):
        self.authenticate_as("member", "user")
        created = self.client.post("/chat/conversations")
        conversation_id = created.json()["id"]
        listed = self.client.get("/chat/conversations")
        self.assertEqual([item["id"] for item in listed.json()["conversations"]], [conversation_id])

        self.authenticate_as("other-member", "user")
        self.assertEqual(self.client.get("/chat/conversations").json()["conversations"], [])
        self.assertEqual(
            self.client.get(f"/chat/conversations/{conversation_id}/messages").status_code,
            404,
        )
        self.assertEqual(
            self.client.delete(f"/chat/conversations/{conversation_id}").status_code,
            404,
        )

        self.authenticate_as("member", "user")
        self.assertEqual(
            self.client.delete(f"/chat/conversations/{conversation_id}").status_code,
            204,
        )
        self.assertEqual(self.client.get("/chat/conversations").json()["conversations"], [])

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
            member_documents = self.client.get("/documents")
            self.authenticate_as("administrator", "admin")
            admin_response = self.client.get("/pdf")
            admin_documents = self.client.get("/documents")

        self.assertEqual(member_response.json(), {"pdfs": [{"id": 2}]})
        self.assertEqual(admin_response.json(), {"pdfs": [{"id": 1}]})
        self.assertEqual(member_documents.json(), {"documents": [{"id": 2}]})
        self.assertEqual(admin_documents.json(), {"documents": [{"id": 1}]})
        self.assertEqual(get_user.call_count, 2)
        get_user.assert_called_with("member")
        self.assertEqual(get_all.call_count, 2)
        get_all.assert_called_with()

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
            member_documents = self.client.get("/vectordb/documents")
            self.authenticate_as("administrator", "admin")
            admin_response = self.client.get("/vectordb/pdf")
            admin_documents = self.client.get("/vectordb/documents")

        self.assertEqual(len(member_response.json()["sources"]), 2)
        self.assertEqual(len(admin_response.json()["sources"]), 3)
        self.assertEqual(member_documents.json(), member_response.json())
        self.assertEqual(admin_documents.json(), admin_response.json())

    def test_ingestion_uses_the_same_routes_with_role_scoped_service_calls(self):
        ingestion_service = StubDocumentIngestionService()
        app.dependency_overrides[get_document_ingestion_service] = lambda: ingestion_service

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

    def test_generic_document_routes_alias_legacy_pdf_routes(self):
        ingestion_service = StubDocumentIngestionService()
        app.dependency_overrides[get_document_ingestion_service] = lambda: ingestion_service
        self.authenticate_as("member", "user")

        generic_list = self.client.get("/documents")
        legacy_list = self.client.get("/pdf")
        generic_ingest = self.client.post("/vectordb/ingest/document/12")
        legacy_ingest = self.client.post("/vectordb/ingest/pdf/13")

        self.assertEqual(generic_list.status_code, 200)
        self.assertEqual(legacy_list.status_code, 200)
        self.assertEqual(generic_ingest.status_code, 200)
        self.assertEqual(legacy_ingest.status_code, 200)
        self.assertEqual(
            ingestion_service.calls,
            [("user_one", (12, "member")), ("user_one", (13, "member"))],
        )

    def test_document_upload_accepts_supported_types_and_reports_rejected_files(self):
        with tempfile.TemporaryDirectory() as directory:
            uploads_dir = Path(directory)
            (uploads_dir / "data").mkdir()
            with (
                patch("app.api.shared.documents.UPLOADS_DIR", uploads_dir),
                patch("app.api.shared.documents.DATA_DIR", uploads_dir / "data"),
                patch("app.api.shared.documents.add_pdf", return_value=42) as add_document,
            ):
                self.authenticate_as("member", "user")
                response = self.client.post(
                    "/documents/upload",
                    files=[
                        ("files", ("notes.md", b"# Notes\n\nA policy.", "text/markdown")),
                        ("files", ("script.exe", b"not supported", "application/octet-stream")),
                    ],
                    data={"is_public": "0"},
                )

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["uploaded"], ["notes.md"])
            self.assertEqual(payload["uploaded_documents"][0]["id"], 42)
            self.assertEqual(payload["uploaded_pdfs"], payload["uploaded_documents"])
            self.assertEqual(len(payload["errors"]), 1)
            add_document.assert_called_once()

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
            "/chat",
            "/chat/history",
            "/user/pdf",
            "/admin/pdf",
            "/user/vectordb/ingest/all",
            "/admin/vectordb/ingest/all",
        ):
            self.assertNotIn(old_path, registered_paths)


if __name__ == "__main__":
    unittest.main()
