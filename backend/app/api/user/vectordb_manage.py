from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasicCredentials
from app.api.user.user_auth import verify_user_credentials
from app.api.dependencies import get_pdf_ingestion_service
from app.application.pdf_ingestion import PdfIngestionService
from app.infrastructure.retrieval import chat_memory, pdf_vector_store
from app.core.logging import log_event

router = APIRouter()

@router.post("/user/vectordb/ingest/all")
def ingest_all(
    credentials: HTTPBasicCredentials = Depends(verify_user_credentials),
    ingestion_service: PdfIngestionService = Depends(get_pdf_ingestion_service),
):
    try:
        ingestion_service.ingest_user_pdfs(credentials.username)
        log_event(credentials.username, "user_ingest_all_pdfs", "all user PDFs ingested")
        return {"detail": "All your PDFs ingested."}
    except Exception as e:
        log_event(credentials.username, "user_ingest_all_pdfs_failed", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/user/vectordb/ingest/pdf/{pdf_id}")
def ingest_pdf_by_id(
    pdf_id: int,
    credentials: HTTPBasicCredentials = Depends(verify_user_credentials),
    ingestion_service: PdfIngestionService = Depends(get_pdf_ingestion_service),
):
    try:
        ingestion_service.ingest_user_pdf_by_id(pdf_id, credentials.username)
        log_event(credentials.username, "user_ingest_pdf_by_id", f"pdf_id={pdf_id}")
        return {"detail": f"PDF {pdf_id} ingested."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        log_event(credentials.username, "user_ingest_pdf_by_id_failed", f"pdf_id={pdf_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/user/vectordb/pdf/all")
def remove_all_pdf_data(credentials: HTTPBasicCredentials = Depends(verify_user_credentials)):
    try:
        pdf_vector_store.clear_pdf_by_user(credentials.username)
        log_event(credentials.username, "user_remove_all_pdf_data", "all user PDF data removed from vectordb")
        return {"detail": "All your PDF data removed from vectordb."}
    except Exception as e:
        log_event(credentials.username, "user_remove_all_pdf_data_failed", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/vectordb/pdf")
def get_available_pdf_data(credentials: HTTPBasicCredentials = Depends(verify_user_credentials)):
    try:
        sources = pdf_vector_store.get_pdf_sources()
        filtered = [s for s in sources if s["ingested_by"] == credentials.username or s["ingested_by"] == "public"]
        log_event(credentials.username, "user_list_vectordb_sources", f"count={len(filtered)}")
        return {"sources": filtered}
    except Exception as e:
        log_event(credentials.username, "user_list_vectordb_sources_failed", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/user/vectordb/memory")
def clear_my_memory(credentials: HTTPBasicCredentials = Depends(verify_user_credentials)):
    try:
        chat_memory.clear_history_by_user(credentials.username)
        log_event(credentials.username, "user_clear_memory", "chat history cleared from vectordb")
        return {"detail": "Your chat history cleared from vectordb."}
    except Exception as e:
        log_event(credentials.username, "user_clear_memory_failed", str(e))
        raise HTTPException(status_code=500, detail=str(e))
