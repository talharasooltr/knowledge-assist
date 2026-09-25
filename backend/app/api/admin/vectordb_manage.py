from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasicCredentials
from app.api.admin.admin_auth import verify_admin_credentials
from app.api.dependencies import get_pdf_ingestion_service
from app.application.pdf_ingestion import PdfIngestionService
from app.infrastructure.retrieval import chat_memory, pdf_vector_store
from app.core.logging import log_event

router = APIRouter()

@router.post("/admin/vectordb/ingest/all")
def ingest_all(
    credentials: HTTPBasicCredentials = Depends(verify_admin_credentials),
    ingestion_service: PdfIngestionService = Depends(get_pdf_ingestion_service),
):
    try:
        ingestion_service.ingest_all_public_pdfs()
        log_event(credentials.username, "admin_ingest_all_pdfs", "all public PDFs ingested")
        return {"detail": "All public PDFs ingested."}
    except Exception as e:
        log_event(credentials.username, "admin_ingest_all_pdfs_failed", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/vectordb/ingest/pdf/{pdf_id}/public")
def ingest_public_pdf_by_id(
    pdf_id: int,
    credentials: HTTPBasicCredentials = Depends(verify_admin_credentials),
    ingestion_service: PdfIngestionService = Depends(get_pdf_ingestion_service),
):
    try:
        ingestion_service.ingest_pdf_by_id(pdf_id, is_public=True)
        log_event(credentials.username, "admin_ingest_public_pdf_by_id", f"pdf_id={pdf_id}")
        return {"detail": f"PDF {pdf_id} ingested as public."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        log_event(credentials.username, "admin_ingest_public_pdf_by_id_failed", f"pdf_id={pdf_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/vectordb/ingest/pdf/{pdf_id}/private")
def ingest_private_pdf_by_id(
    pdf_id: int,
    user_id: str,
    credentials: HTTPBasicCredentials = Depends(verify_admin_credentials),
    ingestion_service: PdfIngestionService = Depends(get_pdf_ingestion_service),
):
    try:
        ingestion_service.ingest_pdf_by_id(pdf_id, user_id=user_id, is_public=False)
        log_event(credentials.username, "admin_ingest_private_pdf_by_id", f"pdf_id={pdf_id}, user_id={user_id}")
        return {"detail": f"PDF {pdf_id} ingested for user '{user_id}'."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        log_event(credentials.username, "admin_ingest_private_pdf_by_id_failed", f"pdf_id={pdf_id}, user_id={user_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/admin/vectordb/pdf/user/{owner}")
def remove_pdf_data_by_user(owner: str, credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    try:
        pdf_vector_store.clear_pdf_by_user(owner)
        log_event(credentials.username, "admin_remove_pdf_data_by_user", f"owner={owner}")
        return {"detail": f"All PDF data for user '{owner}' removed from vectordb."}
    except Exception as e:
        log_event(credentials.username, "admin_remove_pdf_data_by_user_failed", f"owner={owner}, error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/vectordb/pdf")
def get_available_pdf_data(credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    try:
        sources = pdf_vector_store.get_pdf_sources()
        log_event(credentials.username, "admin_list_vectordb_sources", f"count={len(sources)}")
        return {"sources": sources}
    except Exception as e:
        log_event(credentials.username, "admin_list_vectordb_sources_failed", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/admin/vectordb/memory")
def clear_all_users_memory(credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    try:
        chat_memory.clear_history_all()
        log_event(credentials.username, "admin_clear_all_users_memory", "all user chat histories cleared from vectordb")
        return {"detail": "All user chat histories cleared from vectordb."}
    except Exception as e:
        log_event(credentials.username, "admin_clear_all_users_memory_failed", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/admin/vectordb/memory/{user_id}")
def clear_user_memory(user_id: str, credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    try:
        chat_memory.clear_history_by_user(user_id)
        log_event(credentials.username, "admin_clear_user_memory", f"user_id={user_id}")
        return {"detail": f"Chat history for user '{user_id}' cleared from vectordb."}
    except Exception as e:
        log_event(credentials.username, "admin_clear_user_memory_failed", f"user_id={user_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
