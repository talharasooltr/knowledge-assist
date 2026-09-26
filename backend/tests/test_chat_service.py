import unittest

from langchain_core.documents import Document

from app.application.chat_service import ChatService


class ChatServiceTests(unittest.TestCase):
    def test_answer_uses_retrieved_context_and_saves_message(self):
        calls = []
        service = ChatService(
            retrieve_memory=lambda user, query, limit: [
                Document(page_content="Memory context")
            ],
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
            save_message=lambda user, role, message, citations: calls.append(
                ("save", user, role, message, citations)
            ),
            get_history=lambda user: [],
            generate_response=lambda prompt: calls.append(("generate", prompt)) or "Answer",
        )

        result = service.answer("casey", "Question")

        self.assertIn("Memory context", result.prompt)
        self.assertIn("Document context", result.prompt)
        self.assertIn("[1] guide.pdf, page 2", result.prompt)
        self.assertEqual(result.response, "Answer")
        self.assertEqual(result.citations, [{"number": 1, "filename": "guide.pdf", "page": 2}])
        self.assertEqual(calls[0], ("generate", result.prompt))
        self.assertEqual(calls[1], ("save", "casey", "user", "Question", []))
        self.assertEqual(calls[2], ("save", "casey", "assistant", "Answer", result.citations))

    def test_answer_handles_empty_retrieval_results(self):
        service = ChatService(
            retrieve_memory=lambda user, query, limit: [],
            retrieve_documents=lambda user, query, limit: [],
            save_message=lambda user, role, message, citations: None,
            get_history=lambda user: [],
            generate_response=lambda prompt: prompt,
        )

        result = service.answer("casey", "Question")

        self.assertIn("No previous conversation found.", result.prompt)
        self.assertIn("No relevant documents found.", result.prompt)
        self.assertEqual(result.citations, [])


if __name__ == "__main__":
    unittest.main()