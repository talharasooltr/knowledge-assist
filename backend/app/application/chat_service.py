from collections.abc import Callable
from dataclasses import dataclass

from langchain_core.documents import Document

from app.application.chat_types import ChatHistoryEntry, ChatRole, CitationData


@dataclass(frozen=True)
class ChatResult:
    response: str
    prompt: str
    citations: list[CitationData]


class ChatService:
    def __init__(
        self,
        retrieve_memory: Callable[[str, str, int], list[Document]],
        retrieve_documents: Callable[[str, str, int], list[Document]],
        save_message: Callable[[str, ChatRole, str, list[CitationData]], None],
        get_history: Callable[[str], list[ChatHistoryEntry]],
        generate_response: Callable[[str], str],
    ) -> None:
        self._retrieve_memory = retrieve_memory
        self._retrieve_documents = retrieve_documents
        self._save_message = save_message
        self._get_history = get_history
        self._generate_response = generate_response

    def answer(self, user_id: str, message: str) -> ChatResult:
        memories = self._retrieve_memory(user_id, message, 3)
        documents = self._retrieve_documents(user_id, message, 3)

        memory_text = "\n".join(document.page_content for document in memories)
        citations: list[CitationData] = []
        citation_numbers: dict[tuple[str, int | None], int] = {}
        document_sections = []
        for document in documents:
            metadata = document.metadata or {}
            filename_value = metadata.get("filename")
            source_value = metadata.get("source")
            filename = next(
                (value for value in (filename_value, source_value) if isinstance(value, str) and value),
                "Document",
            )
            page_value = metadata.get("page")
            if isinstance(page_value, int) and not isinstance(page_value, bool):
                page = page_value + 1
            elif isinstance(page_value, str):
                try:
                    page = int(page_value) + 1
                except ValueError:
                    page = None
            else:
                page = None

            key = (filename, page)
            if key not in citation_numbers:
                citation_numbers[key] = len(citations) + 1
                citations.append({"number": len(citations) + 1, "filename": filename, "page": page})
            number = citation_numbers[key]
            page_label = f", page {page}" if page is not None else ""
            document_sections.append(
                f"[{number}] {filename}{page_label}\n{document.page_content}"
            )
        document_text = "\n\n".join(document_sections)
        prompt = f"""
    Previous conversation:
    {memory_text or "No previous conversation found."}

    Relevant documents:
    {document_text or "No relevant documents found."}

    Cite supporting documents in the answer using their bracketed numbers, such as [1].
    If the documents do not support an answer, say so clearly.

    User: {message}
    Answer:
    """

        response = self._generate_response(prompt)
        self._save_message(user_id, "user", message, [])
        self._save_message(user_id, "assistant", response, citations)
        return ChatResult(response=response, prompt=prompt, citations=citations)

    def history(self, user_id: str) -> list[ChatHistoryEntry]:
        return self._get_history(user_id)