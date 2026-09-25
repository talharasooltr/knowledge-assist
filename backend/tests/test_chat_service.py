import unittest
from types import SimpleNamespace

from app.application.chat_service import ChatService


class ChatServiceTests(unittest.TestCase):
    def test_answer_uses_retrieved_context_and_saves_message(self):
        calls = []
        service = ChatService(
            retrieve_memory=lambda user, query, limit: [
                SimpleNamespace(page_content="Memory context")
            ],
            retrieve_documents=lambda user, query, limit: [
                SimpleNamespace(page_content="Document context")
            ],
            save_message=lambda user, message: calls.append(("save", user, message)),
            get_history=lambda user: [],
            generate_response=lambda prompt: calls.append(("generate", prompt)) or "Answer",
        )

        result = service.answer("casey", "Question")

        self.assertIn("Memory context", result.prompt)
        self.assertIn("Document context", result.prompt)
        self.assertEqual(result.response, "Answer")
        self.assertEqual(calls[0], ("save", "casey", "Question"))
        self.assertEqual(calls[1][0], "generate")

    def test_answer_handles_empty_retrieval_results(self):
        service = ChatService(
            retrieve_memory=lambda user, query, limit: [],
            retrieve_documents=lambda user, query, limit: [],
            save_message=lambda user, message: None,
            get_history=lambda user: [],
            generate_response=lambda prompt: prompt,
        )

        result = service.answer("casey", "Question")

        self.assertIn("No previous conversation found.", result.prompt)
        self.assertIn("No relevant documents found.", result.prompt)


if __name__ == "__main__":
    unittest.main()