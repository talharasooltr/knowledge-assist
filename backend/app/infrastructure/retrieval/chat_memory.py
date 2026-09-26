import time
import uuid

from langchain_core.documents import Document
from sqlalchemy import delete, select

from app.application.chat_types import ChatHistoryEntry, ChatRole, CitationData
from app.core.json_types import JSONValue
from app.infrastructure.db.models import ChatMemory
from app.infrastructure.db.session import get_session
from app.infrastructure.providers.embeddings import get_embedding

CHAT_HISTORY_LIMIT = 20


def save_chat_message(
    user_id: str,
    role: ChatRole,
    message: str,
    citations: list[CitationData],
) -> None:
    timestamp = time.time()
    with get_session() as session:
        memory = ChatMemory(
            id=str(uuid.uuid4()),
            user_id=user_id,
            content=message,
            embedding=get_embedding().embed_query(message),
            timestamp=timestamp,
            metadata_={
                "user_id": user_id,
                "timestamp": timestamp,
                "role": role,
                "citations": citations,
            },
        )
        session.add(memory)
        old_ids = session.scalars(
            select(ChatMemory.id)
            .where(ChatMemory.user_id == user_id)
            .order_by(ChatMemory.timestamp.desc())
            .offset(CHAT_HISTORY_LIMIT)
        ).all()
        if old_ids:
            session.execute(delete(ChatMemory).where(ChatMemory.id.in_(old_ids)))


def retrieve_user_memory(user_id: str, query: str, k: int = 3) -> list[Document]:
    query_embedding = get_embedding().embed_query(query)
    with get_session() as session:
        memories = session.scalars(
            select(ChatMemory)
            .where(ChatMemory.user_id == user_id)
            .order_by(ChatMemory.embedding.cosine_distance(query_embedding))
            .limit(k)
        ).all()
        return [Document(page_content=item.content, metadata=item.metadata_ or {}) for item in memories]


def _history_citations(value: JSONValue) -> list[CitationData]:
    if not isinstance(value, list):
        return []

    citations: list[CitationData] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        number = item.get("number")
        filename = item.get("filename")
        page_value = item.get("page")
        if isinstance(number, bool) or not isinstance(number, int) or not isinstance(filename, str):
            continue
        page = page_value if isinstance(page_value, int) and not isinstance(page_value, bool) else None
        citations.append({"number": number, "filename": filename, "page": page})
    return citations


def get_all_history(user_id: str) -> list[ChatHistoryEntry]:
    with get_session() as session:
        memories = session.scalars(
            select(ChatMemory)
            .where(ChatMemory.user_id == user_id)
            .order_by(ChatMemory.timestamp)
        ).all()
        history: list[ChatHistoryEntry] = []
        for memory in memories:
            metadata = memory.metadata_ or {}
            role_value = metadata.get("role")
            role: ChatRole = role_value if role_value in ("user", "assistant") else "user"
            history.append(
                {
                    "role": role,
                    "content": memory.content,
                    "citations": _history_citations(metadata.get("citations", [])),
                }
            )
        return history


def clear_history_by_user(user_id: str) -> None:
    with get_session() as session:
        session.execute(delete(ChatMemory).where(ChatMemory.user_id == user_id))


def clear_history_all() -> None:
    with get_session() as session:
        session.execute(delete(ChatMemory))


def get_available_user_ids() -> list[str]:
    from sqlalchemy import distinct

    with get_session() as session:
        return list(
            session.scalars(
                select(distinct(ChatMemory.user_id)).order_by(ChatMemory.user_id)
            )
        )