from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_pdf_ingestion_service
from app.api.session_auth import SessionPrincipal, require_session
from app.application.pdf_ingestion import PdfIngestionService
from app.core.logging import log_event
from app.infrastructure.retrieval import pdf_vector_store

router = APIRouter()


@router.post("/vectordb/ingest/all")
def ingest_all(
    principal: SessionPrincipal = Depends(require_session),
    ingestion_service: PdfIngestionService = Depends(get_pdf_ingestion_service),
):
    if principal.role == "admin":
        ingestion_service.ingest_all_public_pdfs()
        detail = "All public PDFs ingested."
    else:
        ingestion_service.ingest_user_pdfs(principal.username)
        detail = "All your PDFs ingested."
    log_event(principal.username, "ingest_all_pdfs", detail)
    return {"detail": detail}


@router.post("/vectordb/ingest/pdf/{pdf_id}")
def ingest_pdf_by_id(
    pdf_id: int,
    principal: SessionPrincipal = Depends(require_session),
    ingestion_service: PdfIngestionService = Depends(get_pdf_ingestion_service),
):
    try:
        if principal.role == "admin":
            ingestion_service.ingest_pdf_by_id(pdf_id)
        else:
            ingestion_service.ingest_user_pdf_by_id(pdf_id, principal.username)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    log_event(principal.username, "ingest_pdf_by_id", f"pdf_id={pdf_id}")
    return {"detail": f"PDF {pdf_id} ingested."}


@router.get("/vectordb/pdf")
def get_available_pdf_data(principal: SessionPrincipal = Depends(require_session)):
    sources = pdf_vector_store.get_pdf_sources()
    if principal.role == "user":
        sources = [
            source
            for source in sources
            if source["ingested_by"] in {principal.username, "public"}
        ]
    log_event(principal.username, "list_vectordb_sources", f"count={len(sources)}")
    return {"sources": sources}


@router.delete("/vectordb/pdf")
def remove_my_pdf_data(principal: SessionPrincipal = Depends(require_session)):
    pdf_vector_store.clear_pdf_by_user(principal.username)
    log_event(principal.username, "remove_pdf_data", "own PDF data removed from vector store")
    return {"detail": "Your PDF data was removed from the vector store."}
