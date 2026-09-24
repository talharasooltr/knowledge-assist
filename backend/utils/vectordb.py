import os
import time
import uuid
from collections.abc import Iterable

from langchain_core.documents import Document
from langchain_openai import AzureOpenAIEmbeddings, OpenAIEmbeddings
from sqlalchemy import delete, distinct, or_, select

from utils.database import get_session
from utils.models import ChatMemory, Pdf, PdfChunk

from utils.config import ENV_FILE

from dotenv import load_dotenv

load_dotenv(ENV_FILE)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").strip().lower()
if LLM_PROVIDER == "openai":
    embedding = OpenAIEmbeddings()
elif LLM_PROVIDER == "azure-openai":
    embedding = AzureOpenAIEmbeddings(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    )
else:
    raise ValueError("LLM_PROVIDER must be 'openai' or 'azure-openai'")

CHAT_HISTORY_LIMIT = 10


def get_embedding():
    return embedding


def _document(content: str, metadata: dict | None) -> Document:
    return Document(page_content=content, metadata=metadata or {})


def save_user_message(user_id: str, message: str) -> None:
    timestamp = time.time()
    with get_session() as session:
        memory = ChatMemory(
            id=str(uuid.uuid4()),
            user_id=user_id,
            content=message,
            embedding=embedding.embed_query(message),
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
    query_embedding = embedding.embed_query(query)
    with get_session() as session:
        memories = session.scalars(
            select(ChatMemory)
            .where(ChatMemory.user_id == user_id)
            .order_by(ChatMemory.embedding.cosine_distance(query_embedding))
            .limit(k)
        ).all()
        return [_document(memory.content, memory.metadata_) for memory in memories]


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


def _chunk_metadata(chunk: Document) -> dict:
    metadata = dict(chunk.metadata or {})
    metadata.setdefault("source", metadata.get("filename"))
    metadata.setdefault("filename", metadata.get("source"))
    metadata.setdefault("user_id", "public")
    metadata.setdefault("is_public", 0)
    return metadata


def insert_new_chunks(chunks: Iterable[Document]) -> bool:
    documents = list(chunks)
    if not documents:
        return True
    texts = [document.page_content for document in documents]
    embeddings = embedding.embed_documents(texts)
    with get_session() as session:
        for index, (document, vector) in enumerate(zip(documents, embeddings)):
            metadata = _chunk_metadata(document)
            session.add(
                PdfChunk(
                    id=str(uuid.uuid4()),
                    content=document.page_content,
                    embedding=vector,
                    source=metadata.get("source"),
                    filename=metadata.get("filename"),
                    user_id=metadata.get("user_id"),
                    is_public=bool(metadata.get("is_public")),
                    metadata_=metadata,
                    chunk_index=index,
                )
            )
    return True


def get_available_user_ids() -> list[str]:
    with get_session() as session:
        return list(session.scalars(select(distinct(ChatMemory.user_id)).order_by(ChatMemory.user_id)))


def get_pdf_sources() -> list[dict]:
    with get_session() as session:
        rows = session.execute(
            select(distinct(PdfChunk.source), PdfChunk.user_id)
            .where(PdfChunk.source.is_not(None), PdfChunk.user_id.is_not(None))
        ).all()
        return [{"source": source, "ingested_by": user_id} for source, user_id in rows]


def retrieve_pdf_for_user(user_id: str, query: str, k: int = 3) -> list[Document]:
    query_embedding = embedding.embed_query(query)
    with get_session() as session:
        chunks = session.scalars(
            select(PdfChunk)
            .where(or_(PdfChunk.user_id == user_id, PdfChunk.is_public.is_(True)))
            .order_by(PdfChunk.embedding.cosine_distance(query_embedding))
            .limit(k)
        ).all()
        return [_document(chunk.content, chunk.metadata_) for chunk in chunks]


def clear_pdf_by_source(source_name: str, user_id: str | None = None) -> None:
    with get_session() as session:
        query = delete(PdfChunk).where(
            or_(PdfChunk.source == source_name, PdfChunk.filename == source_name)
        )
        if user_id is not None:
            query = query.where(PdfChunk.user_id == user_id)
        session.execute(query)


def clear_pdf_by_user(user_id: str) -> None:
    with get_session() as session:
        session.execute(delete(PdfChunk).where(PdfChunk.user_id == user_id))


def clear_all_pdf() -> None:
    with get_session() as session:
        session.execute(delete(PdfChunk))
