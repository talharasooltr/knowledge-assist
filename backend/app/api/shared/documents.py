from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.dependencies import get_pdf_deletion_service
from app.api.session_auth import SessionPrincipal, require_session
from app.application.pdf_deletion import (
    PdfDeletionPendingError,
    PdfDeletionService,
    PdfNotFoundError,
)
from app.core.config import MAX_DOCUMENT_UPLOAD_BYTES, UPLOADS_DIR
from app.core.document_formats import DOCUMENT_FORMATS, document_extension
from app.core.file_uploads import (
    InvalidDocumentUploadError,
    UploadTooLargeError,
    save_document_stream,
)
from app.core.logging import log_event
from app.infrastructure.db.repository import add_pdf, get_all_pdfs, get_pdfs_by_user

DATA_DIR = UPLOADS_DIR / "data"

router = APIRouter()


@router.post("/documents/upload")
@router.post("/pdf/upload", include_in_schema=False)
def upload_documents(
    files: Annotated[list[UploadFile], File(...)],
    is_public: Annotated[int, Form(ge=0, le=1)] = 0,
    principal: SessionPrincipal = Depends(require_session),
):
    uploaded = []
    uploaded_documents = []
    errors = []
    uploaded_by = "admin" if principal.role == "admin" else principal.username

    for file in files:
        filename = (file.filename or "").replace("\\", "/").rsplit("/", 1)[-1]
        extension = document_extension(filename)
        if extension not in DOCUMENT_FORMATS or len(filename) > 512:
            supported = ", ".join(DOCUMENT_FORMATS)
            errors.append({
                "filename": filename,
                "error": f"Unsupported document type. Supported extensions: {supported}.",
            })
            continue

        visibility_directory = "public" if is_public else "private"
        db_path = Path(visibility_directory) / f"{uuid4().hex}{extension}"
        file_path = UPLOADS_DIR / "data" / db_path
        (DATA_DIR / visibility_directory).mkdir(parents=True, exist_ok=True)
        try:
            save_document_stream(
                file.file,
                file_path,
                MAX_DOCUMENT_UPLOAD_BYTES,
                extension,
            )
            pdf_id = add_pdf(filename, uploaded_by, is_public, str(db_path))
        except (UploadTooLargeError, InvalidDocumentUploadError) as error:
            errors.append({"filename": filename, "error": str(error)})
            continue
        except Exception:
            file_path.unlink(missing_ok=True)
            raise

        uploaded.append(filename)
        uploaded_documents.append({
            "id": pdf_id,
            "filename": filename,
            "uploaded_by": uploaded_by,
            "is_public": bool(is_public),
            "is_indexed": False,
        })
        log_event(
            principal.username,
            "upload_document",
            f"filename={filename}, is_public={is_public}",
        )

    if not uploaded and not errors:
        raise HTTPException(status_code=400, detail="No documents were provided.")
    return {
        "uploaded": uploaded,
        "uploaded_documents": uploaded_documents,
        "uploaded_pdfs": uploaded_documents,
        "errors": errors,
    }


def _list_documents(principal: SessionPrincipal) -> list[dict]:
    documents = (
        get_all_pdfs()
        if principal.role == "admin"
        else get_pdfs_by_user(principal.username)
    )
    log_event(principal.username, "list_documents", f"count={len(documents)}")
    return documents


@router.get("/documents")
def list_documents(principal: SessionPrincipal = Depends(require_session)):
    return {"documents": _list_documents(principal)}


@router.get("/pdf", include_in_schema=False)
def list_pdfs(principal: SessionPrincipal = Depends(require_session)):
    return {"pdfs": _list_documents(principal)}


@router.delete("/documents/{document_id}")
@router.delete("/pdf/{document_id}", include_in_schema=False)
def delete_document(
    document_id: int,
    principal: SessionPrincipal = Depends(require_session),
    deletion_service: PdfDeletionService = Depends(get_pdf_deletion_service),
):
    owner_id = None if principal.role == "admin" else principal.username
    try:
        pdf = deletion_service.delete_pdf(document_id, owner_id)
    except PdfNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except PdfDeletionPendingError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=500, detail="Stored document path is invalid.") from error
    except OSError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    log_event(principal.username, "delete_document", f"document_id={document_id}")
    return {"deleted": {"id": document_id, "filename": pdf["filename"]}}
