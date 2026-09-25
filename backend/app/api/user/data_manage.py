from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.security import HTTPBasicCredentials
from typing import List
from app.api.user.user_auth import verify_user_credentials
from app.api.dependencies import get_pdf_deletion_service
from app.application.pdf_deletion import (
    PdfDeletionPendingError,
    PdfDeletionService,
    PdfNotFoundError,
)
import app.infrastructure.db.repository as db
from app.core.logging import log_event

from app.core.config import MAX_PDF_UPLOAD_BYTES, UPLOADS_DIR
from app.core.file_uploads import InvalidPdfUploadError, UploadTooLargeError, save_pdf_stream

DATA_DIR = UPLOADS_DIR / "data"

router = APIRouter()

@router.post("/user/pdf/upload")
def upload_pdf(
    files: List[UploadFile] = File(...),
    credentials: HTTPBasicCredentials = Depends(verify_user_credentials),
    is_public: int = Form(0, ge=0, le=1)
):
    uploaded = []
    uploaded_pdfs = []
    errors = []
    for file in files:
        filename = (file.filename or "").replace("\\", "/").rsplit("/", 1)[-1]
        if not filename.lower().endswith(".pdf") or len(filename) > 512:
            errors.append({"filename": filename, "error": "A valid PDF filename is required."})
            continue
        if is_public:
            save_dir = DATA_DIR / "public"
            db_path = Path("public") / f"{uuid4().hex}.pdf"
        else:
            save_dir = DATA_DIR / "private"
            db_path = Path("private") / f"{uuid4().hex}.pdf"
        save_dir.mkdir(parents=True, exist_ok=True)
        file_path = UPLOADS_DIR / "data" / db_path
        try:
            save_pdf_stream(file.file, file_path, MAX_PDF_UPLOAD_BYTES)
            pdf_id = db.add_pdf(filename, credentials.username, is_public, str(db_path))
        except UploadTooLargeError as error:
            errors.append({"filename": filename, "error": str(error)})
            continue
        except InvalidPdfUploadError as error:
            errors.append({"filename": filename, "error": str(error)})
            continue
        except Exception:
            file_path.unlink(missing_ok=True)
            raise
        uploaded.append(filename)
        uploaded_pdfs.append({
            "id": pdf_id,
            "filename": filename,
            "uploaded_by": credentials.username,
            "is_public": bool(is_public),
            "is_indexed": False,
        })
        log_event(credentials.username, "upload_pdf", f"filename={filename}, is_public={is_public}")
    if not uploaded and not errors:
        raise HTTPException(status_code=400, detail="No PDFs were provided.")
    return {"uploaded": uploaded, "uploaded_pdfs": uploaded_pdfs, "errors": errors}

@router.get("/user/pdf")
def list_pdfs(credentials: HTTPBasicCredentials = Depends(verify_user_credentials)):
    pdfs = db.get_pdfs_by_user(credentials.username)
    log_event(credentials.username, "list_pdfs", f"count={len(pdfs)}")
    return {"pdfs": pdfs}

@router.delete("/user/pdf/{pdf_id}")
def delete_pdf(
    pdf_id: int,
    credentials: HTTPBasicCredentials = Depends(verify_user_credentials),
    deletion_service: PdfDeletionService = Depends(get_pdf_deletion_service),
):
    try:
        pdf = deletion_service.delete_pdf(pdf_id, credentials.username)
    except PdfNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except PdfDeletionPendingError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=500, detail="Stored PDF path is invalid.") from error
    except OSError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    log_event(credentials.username, "delete_pdf", f"pdf_id={pdf_id}")
    return {"deleted": {"id": pdf_id, "filename": pdf["filename"]}}
