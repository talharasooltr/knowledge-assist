from typing import Literal

from pydantic import BaseModel


class ChatRequest(BaseModel):
    user_id: str
    message: str


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