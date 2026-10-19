from datetime import datetime
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


class ChatConversation(TypedDict):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime