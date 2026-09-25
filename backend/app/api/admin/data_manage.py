from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Body, Form
from fastapi.security import HTTPBasicCredentials
from typing import List
from app.api.admin.admin_auth import verify_admin_credentials
from app.infrastructure.db.repository import add_pdf, get_all_pdfs, delete_pdf_by_filename, get_all_ingested_pdfs, get_pdf_filepath_by_filename
from app.core.logging import log_event

from app.core.config import UPLOADS_DIR

DATA_DIR = UPLOADS_DIR / "data"

router = APIRouter()

# upload pdfs list by admin
@router.post("/admin/pdf/upload")
def upload_pdf(
    files: List[UploadFile] = File(...),
    is_public: int = Form(0),
    credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)
):
    uploaded = []
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            continue
        if is_public:
            save_dir = DATA_DIR / "public"
            db_path = Path("public") / file.filename
            uploaded_by = "admin"
        else:
            uploaded_by = "admin"
            save_dir = DATA_DIR / uploaded_by
            db_path = Path(uploaded_by) / file.filename
        save_dir.mkdir(parents=True, exist_ok=True)
        file_path = save_dir / file.filename
        with file_path.open("wb") as f:
            f.write(file.file.read())
        add_pdf(file.filename, uploaded_by, is_public, str(db_path))
        uploaded.append(file.filename)
        log_event(credentials.username, "admin_upload_pdf", f"filename={file.filename}, is_public={is_public}")
    if not uploaded:
        raise HTTPException(status_code=400, detail="No valid PDFs uploaded.")
    return {"uploaded": uploaded}

# get all pdfs uploaded by admin and users with some information like uploaded_by, is_public.
@router.get("/admin/pdf")
def list_pdfs(credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    pdfs = get_all_pdfs()
    log_event(credentials.username, "admin_list_pdfs", f"count={len(pdfs)}")
    return {"pdfs": pdfs}

# delete pdfs list by filename
@router.post("/admin/pdf/delete")
def delete_pdf(
    data: dict = Body(...),
    credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)
):
    filenames = data.get("filenames")
    if not filenames or not isinstance(filenames, list):
        raise HTTPException(status_code=400, detail="Missing or invalid 'filenames' (must be a list).")
    deleted = []
    errors = []
    for filename in filenames:
        from app.infrastructure.db.repository import get_all_pdfs
        pdfs = get_all_pdfs()
        pdf_info = next((pdf for pdf in pdfs if pdf["filename"] == filename), None)
        if not pdf_info:
            errors.append({"filename": filename, "error": "Not found in database"})
            continue
        if pdf_info["is_public"] == 1:
            abs_file_path = DATA_DIR / "public" / filename
        else:
            abs_file_path = DATA_DIR / pdf_info["uploaded_by"] / filename
        if not abs_file_path.exists():
            errors.append({"filename": filename, "error": "File not found on disk"})
            continue
        try:
            abs_file_path.unlink()
        except Exception as e:
            errors.append({"filename": filename, "error": str(e)})
            continue
        from app.infrastructure.db.repository import delete_pdf_by_id
        fileid = pdf_info["id"]
        success = delete_pdf_by_id(fileid)
        if not success:
            errors.append({"filename": filename, "error": "Failed to delete from database"})
            continue
        deleted.append(filename)
        log_event(credentials.username, "admin_delete_pdf", f"filename={filename}")
    return {"deleted": deleted, "errors": errors}

@router.post("/admin/pdf/delete_public")
def delete_all_public_pdfs(credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    from app.infrastructure.db.repository import get_all_pdfs
    deleted = []
    errors = []
    pdfs = get_all_pdfs()
    for pdf in pdfs:
        if pdf["is_public"] != 1:
            continue
        filename = pdf["filename"]
        abs_file_path = DATA_DIR / "public" / filename
        if not abs_file_path.exists():
            errors.append({"filename": filename, "error": "File not found on disk"})
            continue
        try:
            abs_file_path.unlink()
        except Exception as e:
            errors.append({"filename": filename, "error": str(e)})
            continue
        from app.infrastructure.db.repository import delete_pdf_by_filename
        success = delete_pdf_by_filename(filename)
        if not success:
            errors.append({"filename": filename, "error": "Failed to delete from database"})
            continue
        deleted.append(filename)
        log_event(credentials.username, "admin_delete_public_pdf", f"filename={filename}")
    return {"deleted": deleted, "errors": errors}
