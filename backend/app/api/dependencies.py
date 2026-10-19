from app.application.chat_service import ChatService
from app.application.pdf_deletion import PdfDeletionService
from app.application.document_ingestion import DocumentIngestionService
from app.core.config import UPLOADS_DIR
from app.infrastructure.db.repository import (
    delete_pdf_by_id,
    get_all_pdfs,
    get_pdf_by_id,
    get_pdfs_by_user,
    ingest,
    request_pdf_deletion,
)
from app.infrastructure.providers.llm import LLM
from app.infrastructure.parsers.documents import parse_document
from app.infrastructure.retrieval.chat_memory import (
    create_conversation,
    delete_conversation,
    get_conversation,
    get_conversation_history,
    list_conversations,
    retrieve_user_memory,
    save_chat_message,
)
from app.infrastructure.retrieval.pdf_vector_store import insert_new_chunks, retrieve_pdf_for_user


def get_chat_service() -> ChatService:
    return ChatService(
        retrieve_memory=retrieve_user_memory,
        retrieve_documents=retrieve_pdf_for_user,
        save_message=save_chat_message,
        get_history=get_conversation_history,
        list_conversations=list_conversations,
        create_conversation=create_conversation,
        get_conversation=get_conversation,
        delete_conversation=delete_conversation,
        generate_response=LLM.predict,
    )


def get_document_ingestion_service() -> DocumentIngestionService:
    return DocumentIngestionService(
        upload_directory=UPLOADS_DIR,
        get_all_documents=get_all_pdfs,
        get_documents_by_user=get_pdfs_by_user,
        parse_document=parse_document,
        save_chunks=insert_new_chunks,
        record_ingestion=ingest,
    )


def get_pdf_deletion_service() -> PdfDeletionService:
    return PdfDeletionService(
        storage_directory=UPLOADS_DIR / "data",
        get_pdf_by_id=get_pdf_by_id,
        request_pdf_deletion=request_pdf_deletion,
        delete_pdf_by_id=delete_pdf_by_id,
    )