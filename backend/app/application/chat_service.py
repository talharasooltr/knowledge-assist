from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ChatResult:
    response: str
    prompt: str


class ChatService:
    def __init__(
        self,
        retrieve_memory: Callable[[str, str, int], list[Any]],
        retrieve_documents: Callable[[str, str, int], list[Any]],
        save_message: Callable[[str, str], None],
        get_history: Callable[[str], list[str]],
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
        document_text = "\n".join(document.page_content for document in documents)
        prompt = f"""
    Previous conversation:
    {memory_text or "No previous conversation found."}

    Relevant documents:
    {document_text or "No relevant documents found."}

    User: {message}
    Answer:
    """

        self._save_message(user_id, message)
        response = self._generate_response(prompt)
        return ChatResult(response=response, prompt=prompt)

    def history(self, user_id: str) -> list[str]:
        return self._get_history(user_id)