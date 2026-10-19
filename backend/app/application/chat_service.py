from collections.abc import Callable
from dataclasses import dataclass

from langchain_core.documents import Document

from app.application.chat_types import ChatConversation, ChatHistoryEntry, ChatRole, CitationData


@dataclass(frozen=True)
class ChatResult:
    response: str
    prompt: str
    citations: list[CitationData]


class ConversationNotFoundError(LookupError):
    pass


class ChatService:
    def __init__(
        self,
        retrieve_memory: Callable[[str, str, str, int], list[Document]],
        retrieve_documents: Callable[[str, str, int], list[Document]],
        save_message: Callable[[str, str, ChatRole, str, list[CitationData]], None],
        get_history: Callable[[str, str], list[ChatHistoryEntry]],
        list_conversations: Callable[[str], list[ChatConversation]],
        create_conversation: Callable[[str], ChatConversation],
        get_conversation: Callable[[str, str], ChatConversation | None],
        delete_conversation: Callable[[str, str], bool],
        generate_response: Callable[[str], str],
    ) -> None:
        self._retrieve_memory = retrieve_memory
        self._retrieve_documents = retrieve_documents
        self._save_message = save_message
        self._get_history = get_history
        self._list_conversations = list_conversations
        self._create_conversation = create_conversation
        self._get_conversation = get_conversation
        self._delete_conversation = delete_conversation
        self._generate_response = generate_response

    def conversations(self, user_id: str) -> list[ChatConversation]:
        return self._list_conversations(user_id)

    def create(self, user_id: str) -> ChatConversation:
        return self._create_conversation(user_id)

    def delete(self, user_id: str, conversation_id: str) -> None:
        if not self._delete_conversation(user_id, conversation_id):
            raise ConversationNotFoundError(conversation_id)

    def answer(self, user_id: str, conversation_id: str, message: str) -> ChatResult:
        if self._get_conversation(user_id, conversation_id) is None:
            raise ConversationNotFoundError(conversation_id)

        memories = self._retrieve_memory(user_id, conversation_id, message, 3)
        documents = self._retrieve_documents(user_id, message, 5)

        memory_text = "\n".join(document.page_content for document in memories)
        citations: list[CitationData] = []
        citation_numbers: dict[tuple[str, int | None, int | None, str | None], int] = {}
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
            page_start_value = metadata.get("page_start", page_value)
            page_end_value = metadata.get("page_end", page_start_value)
            if isinstance(page_start_value, int) and not isinstance(page_start_value, bool):
                page = page_start_value + 1
            elif isinstance(page_start_value, str):
                try:
                    page = int(page_start_value) + 1
                except ValueError:
                    page = None
            else:
                page = None
            if isinstance(page_end_value, int) and not isinstance(page_end_value, bool):
                page_end = page_end_value + 1
            elif isinstance(page_end_value, str):
                try:
                    page_end = int(page_end_value) + 1
                except ValueError:
                    page_end = None
            else:
                page_end = None
            if page_end == page:
                page_end = None

            section_value = metadata.get("section")
            section = section_value if isinstance(section_value, str) and section_value else None

            key = (filename, page, page_end, section)
            if key not in citation_numbers:
                citation_numbers[key] = len(citations) + 1
                citation: CitationData = {
                    "number": len(citations) + 1,
                    "filename": filename,
                    "page": page,
                    "page_end": page_end,
                    "section": section,
                }
                citations.append(citation)
            number = citation_numbers[key]
            page_label = ""
            if page is not None:
                page_label = f", pages {page}-{page_end}" if page_end else f", page {page}"
            section_label = f", section {section}" if section else ""
            document_sections.append(
                f"[{number}] {filename}{page_label}{section_label}\n{document.page_content}"
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
        self._save_message(user_id, conversation_id, "user", message, [])
        self._save_message(user_id, conversation_id, "assistant", response, citations)
        return ChatResult(response=response, prompt=prompt, citations=citations)

    def history(self, user_id: str, conversation_id: str) -> list[ChatHistoryEntry]:
        if self._get_conversation(user_id, conversation_id) is None:
            raise ConversationNotFoundError(conversation_id)
        return self._get_history(user_id, conversation_id)