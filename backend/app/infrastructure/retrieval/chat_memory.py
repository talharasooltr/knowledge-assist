import time
import uuid

from langchain_core.documents import Document
from sqlalchemy import delete, select

from app.infrastructure.db.models import ChatMemory
from app.infrastructure.db.session import get_session
from app.infrastructure.providers.embeddings import get_embedding

CHAT_HISTORY_LIMIT = 10


def save_user_message(user_id: str, message: str) -> None:
    timestamp = time.time()
    with get_session() as session:
        memory = ChatMemory(
            id=str(uuid.uuid4()),
            user_id=user_id,
            content=message,
            embedding=get_embedding().embed_query(message),
            timestamp=timestamp,
            metadata_={"user_id": user_id, "timestamp": timestamp},
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


def get_all_history(user_id: str) -> list[str]:
    with get_session() as session:
        memories = session.scalars(
            select(ChatMemory)
            .where(ChatMemory.user_id == user_id)
            .order_by(ChatMemory.timestamp)
        ).all()
        return [memory.content for memory in memories]


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