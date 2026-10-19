from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_document_ingestion_service
from app.api.session_auth import SessionPrincipal, require_session
from app.application.document_ingestion import (
    DocumentIngestionService,
    DocumentNotFoundError,
)
from app.core.logging import log_event
from app.infrastructure.parsers.documents import DocumentParsingError
from app.infrastructure.retrieval import pdf_vector_store

router = APIRouter()


@router.post("/vectordb/ingest/documents")
@router.post("/vectordb/ingest/all", include_in_schema=False)
def ingest_all(
    principal: SessionPrincipal = Depends(require_session),
    ingestion_service: DocumentIngestionService = Depends(get_document_ingestion_service),
):
    if principal.role == "admin":
        ingestion_service.ingest_all_public_documents()
        detail = "All public documents ingested."
    else:
        ingestion_service.ingest_user_documents(principal.username)
        detail = "All your documents ingested."
    log_event(principal.username, "ingest_all_documents", detail)
    return {"detail": detail}


@router.post("/vectordb/ingest/document/{document_id}")
@router.post("/vectordb/ingest/pdf/{document_id}", include_in_schema=False)
def ingest_document_by_id(
    document_id: int,
    principal: SessionPrincipal = Depends(require_session),
    ingestion_service: DocumentIngestionService = Depends(get_document_ingestion_service),
):
    try:
        if principal.role == "admin":
            ingestion_service.ingest_document_by_id(document_id)
        else:
            ingestion_service.ingest_user_document_by_id(document_id, principal.username)
    except DocumentNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except DocumentParsingError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    log_event(principal.username, "ingest_document_by_id", f"document_id={document_id}")
    return {"detail": f"Document {document_id} ingested."}


@router.get("/vectordb/documents")
@router.get("/vectordb/pdf", include_in_schema=False)
def get_available_document_data(principal: SessionPrincipal = Depends(require_session)):
    sources = pdf_vector_store.get_pdf_sources()
    if principal.role == "user":
        sources = [
            source
            for source in sources
            if source["ingested_by"] in {principal.username, "public"}
        ]
    log_event(principal.username, "list_document_vector_sources", f"count={len(sources)}")
    return {"sources": sources}


@router.delete("/vectordb/documents")
@router.delete("/vectordb/pdf", include_in_schema=False)
def remove_my_document_data(principal: SessionPrincipal = Depends(require_session)):
    pdf_vector_store.clear_pdf_by_user(principal.username)
    log_event(
        principal.username,
        "remove_document_data",
        "own document data removed from vector store",
    )
    return {"detail": "Your document data was removed from the vector store."}
