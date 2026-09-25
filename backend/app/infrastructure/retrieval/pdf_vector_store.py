import uuid
from collections.abc import Iterable

from langchain_core.documents import Document
from sqlalchemy import delete, distinct, or_, select

from app.infrastructure.db.models import IngestState, Pdf, PdfChunk
from app.infrastructure.db.session import get_session
from app.infrastructure.providers.embeddings import get_embedding


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
    if any(document.metadata.get("pdf_id") is None for document in documents):
        raise ValueError("Every indexed PDF chunk must include a PDF ID.")
    vectors = get_embedding().embed_documents([document.page_content for document in documents])
    with get_session() as session:
        pdf_ids = {
            document.metadata.get("pdf_id")
            for document in documents
            if document.metadata.get("pdf_id") is not None
        }
        if pdf_ids:
            session.execute(delete(PdfChunk).where(PdfChunk.pdf_id.in_(pdf_ids)))
        for index, (document, vector) in enumerate(zip(documents, vectors)):
            metadata = _chunk_metadata(document)
            session.add(
                PdfChunk(
                    id=str(uuid.uuid4()),
                    pdf_id=metadata.get("pdf_id"),
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


def get_pdf_sources() -> list[dict]:
    with get_session() as session:
        rows = session.execute(
            select(distinct(PdfChunk.source), PdfChunk.user_id)
            .where(PdfChunk.source.is_not(None), PdfChunk.user_id.is_not(None))
        ).all()
        return [{"source": source, "ingested_by": user_id} for source, user_id in rows]


def retrieve_pdf_for_user(user_id: str, query: str, k: int = 3) -> list[Document]:
    query_embedding = get_embedding().embed_query(query)
    with get_session() as session:
        chunks = session.scalars(
            select(PdfChunk)
            .join(PdfChunk.pdf)
            .where(Pdf.deletion_requested.is_(False))
            .where(or_(PdfChunk.user_id == user_id, PdfChunk.is_public.is_(True)))
            .order_by(PdfChunk.embedding.cosine_distance(query_embedding))
            .limit(k)
        ).all()
        return [Document(page_content=chunk.content, metadata=chunk.metadata_ or {}) for chunk in chunks]


def clear_pdf_by_user(user_id: str) -> None:
    with get_session() as session:
        session.execute(delete(PdfChunk).where(PdfChunk.user_id == user_id))
        session.execute(delete(IngestState).where(IngestState.ingested_by == user_id))


def clear_all_pdf() -> None:
    with get_session() as session:
        session.execute(delete(PdfChunk))