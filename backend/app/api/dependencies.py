from app.application.chat_service import ChatService
from app.application.pdf_ingestion import PdfIngestionService
from app.core.config import UPLOADS_DIR
from app.infrastructure.db.repository import get_all_pdfs, get_pdfs_by_user, ingest
from app.infrastructure.providers.llm import LLM
from app.infrastructure.parsers.pdf import parse_pdf
from app.infrastructure.retrieval.chat_memory import (
    get_all_history,
    retrieve_user_memory,
    save_user_message,
)
from app.infrastructure.retrieval.pdf_vector_store import insert_new_chunks, retrieve_pdf_for_user


def get_chat_service() -> ChatService:
    return ChatService(
        retrieve_memory=retrieve_user_memory,
        retrieve_documents=retrieve_pdf_for_user,
        save_message=save_user_message,
        get_history=get_all_history,
        generate_response=LLM.predict,
    )


def get_pdf_ingestion_service() -> PdfIngestionService:
    return PdfIngestionService(
        upload_directory=UPLOADS_DIR,
        get_all_pdfs=get_all_pdfs,
        get_pdfs_by_user=get_pdfs_by_user,
        parse_pdf=parse_pdf,
        save_chunks=insert_new_chunks,
        record_ingestion=ingest,
    )