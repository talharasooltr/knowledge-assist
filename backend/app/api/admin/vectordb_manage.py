from fastapi import APIRouter, Depends, HTTPException
from app.api.admin.admin_auth import require_admin_session
from app.api.dependencies import get_document_ingestion_service
from app.api.session_auth import SessionPrincipal
from app.application.document_ingestion import (
    DocumentIngestionService,
    DocumentNotFoundError,
)
from app.infrastructure.parsers.documents import DocumentParsingError
from app.infrastructure.retrieval import chat_memory, pdf_vector_store
from app.core.logging import log_event

router = APIRouter()

@router.post("/admin/vectordb/ingest/document/{document_id}/public")
@router.post("/admin/vectordb/ingest/pdf/{document_id}/public", include_in_schema=False)
def ingest_public_document_by_id(
    document_id: int,
    principal: SessionPrincipal = Depends(require_admin_session),
    ingestion_service: DocumentIngestionService = Depends(get_document_ingestion_service),
):
    try:
        ingestion_service.ingest_document_by_id(document_id, is_public=True)
        log_event(
            principal.username,
            "admin_ingest_public_document_by_id",
            f"document_id={document_id}",
        )
        return {"detail": f"Document {document_id} ingested as public."}
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DocumentParsingError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        log_event(
            principal.username,
            "admin_ingest_public_document_by_id_failed",
            f"document_id={document_id}, error={str(e)}",
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/vectordb/ingest/document/{document_id}/private")
@router.post("/admin/vectordb/ingest/pdf/{document_id}/private", include_in_schema=False)
def ingest_private_document_by_id(
    document_id: int,
    user_id: str,
    principal: SessionPrincipal = Depends(require_admin_session),
    ingestion_service: DocumentIngestionService = Depends(get_document_ingestion_service),
):
    try:
        ingestion_service.ingest_document_by_id(document_id, user_id=user_id, is_public=False)
        log_event(
            principal.username,
            "admin_ingest_private_document_by_id",
            f"document_id={document_id}, user_id={user_id}",
        )
        return {"detail": f"Document {document_id} ingested for user '{user_id}'."}
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DocumentParsingError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        log_event(
            principal.username,
            "admin_ingest_private_document_by_id_failed",
            f"document_id={document_id}, user_id={user_id}, error={str(e)}",
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/admin/vectordb/documents/user/{owner}")
@router.delete("/admin/vectordb/pdf/user/{owner}", include_in_schema=False)
def remove_document_data_by_user(
    owner: str,
    principal: SessionPrincipal = Depends(require_admin_session),
):
    try:
        pdf_vector_store.clear_pdf_by_user(owner)
        log_event(principal.username, "admin_remove_document_data_by_user", f"owner={owner}")
        return {"detail": f"All document data for user '{owner}' removed from vectordb."}
    except Exception as e:
        log_event(
            principal.username,
            "admin_remove_document_data_by_user_failed",
            f"owner={owner}, error={str(e)}",
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/admin/vectordb/memory")
def clear_all_users_memory(principal: SessionPrincipal = Depends(require_admin_session)):
    try:
        chat_memory.clear_history_all()
        log_event(principal.username, "admin_clear_all_users_memory", "all user chat histories cleared from vectordb")
        return {"detail": "All user chat histories cleared from vectordb."}
    except Exception as e:
        log_event(principal.username, "admin_clear_all_users_memory_failed", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/admin/vectordb/memory/{user_id}")
def clear_user_memory(user_id: str, principal: SessionPrincipal = Depends(require_admin_session)):
    try:
        chat_memory.clear_history_by_user(user_id)
        log_event(principal.username, "admin_clear_user_memory", f"user_id={user_id}")
        return {"detail": f"Chat history for user '{user_id}' cleared from vectordb."}
    except Exception as e:
        log_event(principal.username, "admin_clear_user_memory_failed", f"user_id={user_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
