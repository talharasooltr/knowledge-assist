from typing import Literal, TypedDict

ChatRole = Literal["user", "assistant"]


class CitationData(TypedDict):
    number: int
    filename: str
    page: int | None


class ChatHistoryEntry(TypedDict):
    role: ChatRole
    content: str
    citations: list[CitationData]