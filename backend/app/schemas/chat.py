from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20_000)


class ChatResponse(BaseModel):
    response: str
    prompt: str
    citations: list["ChatCitation"] = []


class ChatCitation(BaseModel):
    number: int
    filename: str
    page: int | None = None


class ChatHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    citations: list["ChatCitation"] = []


class ChatHistoryResponse(BaseModel):
    user_id: str
    history: list[ChatHistoryMessage]


class ChatConversationSummary(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ChatConversationListResponse(BaseModel):
    conversations: list[ChatConversationSummary]


class ChatConversationHistoryResponse(BaseModel):
    conversation_id: UUID
    history: list[ChatHistoryMessage]