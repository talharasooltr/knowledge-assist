import logging
from pathlib import Path
from collections.abc import Callable

from langchain_core.documents import Document


logger = logging.getLogger(__name__)


class PdfIngestionService:
    def __init__(
        self,
        upload_directory: Path,
        get_all_pdfs: Callable[[], list[dict]],
        get_pdfs_by_user: Callable[[str], list[dict]],
        parse_pdf: Callable[[Path], list[Document]],
        save_chunks: Callable[[list[Document]], bool],
        record_ingestion: Callable[[str, str, int, int | None], int],
    ) -> None:
        self._upload_directory = upload_directory
        self._get_all_pdfs = get_all_pdfs
        self._get_pdfs_by_user = get_pdfs_by_user
        self._parse_pdf = parse_pdf
        self._save_chunks = save_chunks
        self._record_ingestion = record_ingestion

    def ingest_all_public_pdfs(self) -> None:
        for pdf in self._get_all_pdfs():
            if pdf["is_public"] and not pdf["is_deleting"]:
                self._ingest_record(pdf, "public", True)

    def ingest_user_pdfs(self, user_id: str, public_only: bool = False) -> None:
        for pdf in self._get_pdfs_by_user(user_id):
            if pdf["is_deleting"] or (public_only and not pdf["is_public"]):
                continue
            self._ingest_record(pdf, user_id, bool(pdf["is_public"]))

    def ingest_pdf_by_id(
        self, pdf_id: int, user_id: str | None = None, is_public: bool | None = None
    ) -> None:
        pdf = next((item for item in self._get_all_pdfs() if item["id"] == pdf_id), None)
        if pdf is None or pdf["is_deleting"]:
            raise ValueError(f"PDF with id {pdf_id} was not found.")
        target_user = user_id or ("public" if is_public else pdf["uploaded_by"])
        target_is_public = bool(is_public) if is_public is not None else bool(pdf["is_public"])
        self._ingest_record(pdf, target_user, target_is_public)

    def ingest_user_pdf_by_id(self, pdf_id: int, user_id: str) -> None:
        pdf = next((item for item in self._get_pdfs_by_user(user_id) if item["id"] == pdf_id), None)
        if pdf is None or pdf["is_deleting"]:
            raise ValueError(f"PDF with id {pdf_id} was not found for this user.")
        self._ingest_record(pdf, user_id, bool(pdf["is_public"]))

    def _ingest_record(self, pdf: dict, user_id: str, is_public: bool) -> None:
        self._try_ingest(
            self._stored_path(pdf),
            pdf["filename"],
            user_id,
            is_public,
            pdf["id"],
        )

    def _try_ingest(
        self,
        file_path: Path,
        filename: str,
        user_id: str,
        is_public: bool,
        pdf_id: int,
    ) -> None:
        try:
            chunks = self._parse_pdf(file_path)
            for chunk in chunks:
                chunk.metadata = {
                    **(chunk.metadata or {}),
                    "user_id": user_id,
                    "filename": filename,
                    "source": filename,
                    "is_public": int(is_public),
                }
                chunk.metadata["pdf_id"] = pdf_id
            self._save_chunks(chunks)
            self._record_ingestion(filename, user_id, int(is_public), pdf_id)
        except Exception:
            logger.exception("Failed to ingest PDF %s", filename)
            raise

    def _stored_path(self, pdf: dict) -> Path:
        return self._upload_directory / "data" / Path(pdf["filepath"])
