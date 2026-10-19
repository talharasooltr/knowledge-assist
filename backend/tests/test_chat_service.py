import unittest
from datetime import datetime, timezone

from langchain_core.documents import Document

from app.application.chat_service import ChatService, ConversationNotFoundError

CONVERSATION_ID = "417ccbf1-6125-4de7-a77e-f4354b097e36"


def make_service(calls):
    conversation = {
        "id": CONVERSATION_ID,
        "title": "Question",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    return ChatService(
        retrieve_memory=lambda user, conversation_id, query, limit: (
            calls.append(("retrieve_memory", user, conversation_id, query, limit))
            or [Document(page_content="Memory context")]
        ),
        retrieve_documents=lambda user, query, limit: [
            Document(
                page_content="Document context",
                metadata={"filename": "guide.pdf", "page": 1},
            ),
            Document(
                page_content="More context from the same page",
                metadata={"filename": "guide.pdf", "page": 1},
            ),
        ],
        save_message=lambda user, conversation_id, role, message, citations: calls.append(
            ("save", user, conversation_id, role, message, citations)
        ),
        get_history=lambda user, conversation_id: [],
        list_conversations=lambda user: [conversation],
        create_conversation=lambda user: conversation,
        get_conversation=lambda user, conversation_id: (
            conversation if user == "casey" and conversation_id == CONVERSATION_ID else None
        ),
        delete_conversation=lambda user, conversation_id: (
            user == "casey" and conversation_id == CONVERSATION_ID
        ),
        generate_response=lambda prompt: calls.append(("generate", prompt)) or "Answer",
    )


class ChatServiceTests(unittest.TestCase):
    def test_answer_uses_retrieved_context_and_saves_message(self):
        calls = []
        service = make_service(calls)

        result = service.answer("casey", CONVERSATION_ID, "Question")

        self.assertIn("Memory context", result.prompt)
        self.assertIn("Document context", result.prompt)
        self.assertIn("[1] guide.pdf, page 2", result.prompt)
        self.assertEqual(result.response, "Answer")
        self.assertEqual(result.citations, [{"number": 1, "filename": "guide.pdf", "page": 2}])
        self.assertIn(("generate", result.prompt), calls)
        self.assertIn(
            ("retrieve_memory", "casey", CONVERSATION_ID, "Question", 3),
            calls,
        )
        self.assertIn(
            ("save", "casey", CONVERSATION_ID, "user", "Question", []),
            calls,
        )
        self.assertIn(
            ("save", "casey", CONVERSATION_ID, "assistant", "Answer", result.citations),
            calls,
        )

    def test_answer_handles_empty_retrieval_results(self):
        calls = []
        service = ChatService(
            retrieve_memory=lambda user, conversation_id, query, limit: [],
            retrieve_documents=lambda user, query, limit: [],
            save_message=lambda user, conversation_id, role, message, citations: None,
            get_history=lambda user, conversation_id: [],
            list_conversations=lambda user: [],
            create_conversation=lambda user: {},
            get_conversation=lambda user, conversation_id: {
                "id": CONVERSATION_ID,
                "title": "Question",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            },
            delete_conversation=lambda user, conversation_id: True,
            generate_response=lambda prompt: prompt,
        )

        result = service.answer("casey", CONVERSATION_ID, "Question")

        self.assertIn("No previous conversation found.", result.prompt)
        self.assertIn("No relevant documents found.", result.prompt)
        self.assertEqual(result.citations, [])

    def test_conversation_access_is_owner_scoped(self):
        service = make_service([])
        with self.assertRaises(ConversationNotFoundError):
            service.history("other-user", CONVERSATION_ID)
        with self.assertRaises(ConversationNotFoundError):
            service.answer("other-user", CONVERSATION_ID, "Question")


if __name__ == "__main__":
    unittest.main()