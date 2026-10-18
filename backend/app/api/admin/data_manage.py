from fastapi import APIRouter, Depends
from app.api.admin.admin_auth import require_admin_session
from app.api.dependencies import get_pdf_deletion_service
from app.api.session_auth import SessionPrincipal
from app.application.pdf_deletion import (
    PdfDeletionService,
)
from app.infrastructure.db.repository import get_all_pdfs
from app.core.logging import log_event

router = APIRouter()

@router.delete("/admin/pdf/public")
def delete_all_public_pdfs(
    principal: SessionPrincipal = Depends(require_admin_session),
    deletion_service: PdfDeletionService = Depends(get_pdf_deletion_service),
):
    deleted = []
    errors = []
    pdfs = get_all_pdfs()
    for pdf in pdfs:
        if pdf["is_public"] != 1:
            continue
        try:
            deletion_service.delete_pdf(pdf["id"])
        except Exception as error:
            errors.append({"id": pdf["id"], "filename": pdf["filename"], "error": str(error)})
            continue
        deleted.append({"id": pdf["id"], "filename": pdf["filename"]})
        log_event(principal.username, "admin_delete_public_pdf", f"pdf_id={pdf['id']}")
    return {"deleted": deleted, "errors": errors}
