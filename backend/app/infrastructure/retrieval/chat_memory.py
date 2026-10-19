import time
import uuid
from datetime import datetime, timezone

from langchain_core.documents import Document
from sqlalchemy import delete, func, select

from app.application.chat_types import ChatConversation, ChatHistoryEntry, ChatRole, CitationData
from app.core.json_types import JSONValue
from app.infrastructure.db.models import ChatConversation as ChatConversationModel
from app.infrastructure.db.models import ChatMemory
from app.infrastructure.db.session import get_session
from app.infrastructure.providers.embeddings import get_embedding


def save_chat_message(
    user_id: str,
    conversation_id: str,
    role: ChatRole,
    message: str,
    citations: list[CitationData],
) -> None:
    timestamp = time.time()
    with get_session() as session:
        memory = ChatMemory(
            id=str(uuid.uuid4()),
            user_id=user_id,
            conversation_id=conversation_id,
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
        conversation = session.scalar(
            select(ChatConversationModel).where(
                ChatConversationModel.id == conversation_id,
                ChatConversationModel.user_id == user_id,
            )
        )
        if conversation is None:
            raise ValueError("Conversation not found for this user.")
        if role == "user" and conversation.title == "New chat":
            conversation.title = _conversation_title(message)
        conversation.updated_at = datetime.now(timezone.utc)


def retrieve_user_memory(
    user_id: str,
    conversation_id: str,
    query: str,
    k: int = 3,
) -> list[Document]:
    query_embedding = get_embedding().embed_query(query)
    with get_session() as session:
        memories = session.scalars(
            select(ChatMemory)
            .where(ChatMemory.user_id == user_id)
            .where(ChatMemory.conversation_id == conversation_id)
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
        page_end_value = item.get("page_end")
        section_value = item.get("section")
        if isinstance(number, bool) or not isinstance(number, int) or not isinstance(filename, str):
            continue
        page = page_value if isinstance(page_value, int) and not isinstance(page_value, bool) else None
        page_end = (
            page_end_value
            if isinstance(page_end_value, int) and not isinstance(page_end_value, bool)
            else None
        )
        section = section_value if isinstance(section_value, str) else None
        citation: CitationData = {
            "number": number,
            "filename": filename,
            "page": page,
            "page_end": page_end,
            "section": section,
        }
        citations.append(citation)
    return citations


def _conversation_title(message: str) -> str:
    title = " ".join(message.split())
    if len(title) <= 80:
        return title or "New chat"
    return f"{title[:77].rstrip()}..."


def _history_entry(memory: ChatMemory) -> ChatHistoryEntry:
    metadata = memory.metadata_ or {}
    role_value = metadata.get("role")
    role: ChatRole = role_value if role_value in ("user", "assistant") else "user"
    return {
        "role": role,
        "content": memory.content,
        "citations": _history_citations(metadata.get("citations", [])),
    }


def _conversation_data(conversation: ChatConversationModel) -> ChatConversation:
    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
    }


def list_conversations(user_id: str) -> list[ChatConversation]:
    with get_session() as session:
        conversations = session.scalars(
            select(ChatConversationModel)
            .where(ChatConversationModel.user_id == user_id)
            .order_by(ChatConversationModel.updated_at.desc(), ChatConversationModel.id)
        ).all()
        return [_conversation_data(conversation) for conversation in conversations]


def create_conversation(user_id: str) -> ChatConversation:
    conversation = ChatConversationModel(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title="New chat",
    )
    with get_session() as session:
        session.add(conversation)
        session.flush()
        return _conversation_data(conversation)


def get_conversation(user_id: str, conversation_id: str) -> ChatConversation | None:
    with get_session() as session:
        conversation = session.scalar(
            select(ChatConversationModel).where(
                ChatConversationModel.id == conversation_id,
                ChatConversationModel.user_id == user_id,
            )
        )
        return _conversation_data(conversation) if conversation is not None else None


def delete_conversation(user_id: str, conversation_id: str) -> bool:
    with get_session() as session:
        result = session.execute(
            delete(ChatConversationModel).where(
                ChatConversationModel.id == conversation_id,
                ChatConversationModel.user_id == user_id,
            )
        )
        return result.rowcount > 0


def get_conversation_history(user_id: str, conversation_id: str) -> list[ChatHistoryEntry]:
    with get_session() as session:
        memories = session.scalars(
            select(ChatMemory)
            .where(
                ChatMemory.user_id == user_id,
                ChatMemory.conversation_id == conversation_id,
            )
            .order_by(ChatMemory.timestamp, ChatMemory.id)
        ).all()
        return [_history_entry(memory) for memory in memories]


def get_all_history(user_id: str) -> list[ChatHistoryEntry]:
    with get_session() as session:
        memories = session.scalars(
            select(ChatMemory)
            .where(ChatMemory.user_id == user_id)
            .order_by(ChatMemory.timestamp, ChatMemory.id)
        ).all()
        return [_history_entry(memory) for memory in memories]


def clear_history_by_user(user_id: str) -> None:
    with get_session() as session:
        session.execute(
            delete(ChatConversationModel).where(ChatConversationModel.user_id == user_id)
        )


def clear_history_all() -> None:
    with get_session() as session:
        session.execute(delete(ChatConversationModel))


def get_available_user_ids() -> list[str]:
    from sqlalchemy import distinct

    with get_session() as session:
        return list(
            session.scalars(
                select(distinct(ChatMemory.user_id)).order_by(ChatMemory.user_id)
            )
        )