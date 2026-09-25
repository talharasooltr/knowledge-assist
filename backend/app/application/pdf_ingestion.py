import logging
from pathlib import Path
from typing import Any, Callable


logger = logging.getLogger(__name__)


class PdfIngestionService:
    def __init__(
        self,
        upload_directory: Path,
        get_all_pdfs: Callable[[], list[dict]],
        get_pdfs_by_user: Callable[[str], list[dict]],
        parse_pdf: Callable[[Path], list[Any]],
        save_chunks: Callable[[list[Any]], bool],
        record_ingestion: Callable[[str, str, int], int],
    ) -> None:
        self._upload_directory = upload_directory
        self._get_all_pdfs = get_all_pdfs
        self._get_pdfs_by_user = get_pdfs_by_user
        self._parse_pdf = parse_pdf
        self._save_chunks = save_chunks
        self._record_ingestion = record_ingestion

    def ingest_all_public_pdfs(self) -> None:
        public_directory = self._upload_directory / "data" / "public"
        if not public_directory.exists():
            return
        for file_path in public_directory.iterdir():
            if file_path.suffix.lower() == ".pdf":
                self._try_ingest(file_path, file_path.name, "public", True)

    def ingest_pdf_as_admin(self, filename: str, user_id: str | None = None) -> None:
        pdf = self._find_pdf(filename, self._get_all_pdfs())
        if pdf is not None:
            target_user = user_id or "public"
            self._try_ingest(
                self._stored_path(pdf), pdf["filename"], target_user, user_id is None
            )

    def ingest_pdf_as_public(self, filename: str) -> None:
        pdf = self._find_pdf(filename, self._get_all_pdfs())
        if pdf is not None:
            path = self._upload_directory / "data" / "public" / filename
            self._try_ingest(path, pdf["filename"], "public", True)

    def ingest_pdf_for_user(self, filename: str, user_id: str) -> None:
        pdf = self._find_pdf(filename, self._get_all_pdfs())
        if pdf is not None:
            self._try_ingest(self._stored_path(pdf), pdf["filename"], user_id, False)

    def ingest_user_pdfs(self, user_id: str, public_only: bool = False) -> None:
        for pdf in self._get_pdfs_by_user(user_id):
            if public_only and not pdf["is_public"]:
                continue
            self._try_ingest(
                self._stored_path(pdf),
                pdf["filename"],
                user_id,
                bool(pdf["is_public"]),
            )

    def ingest_user_pdf(self, filename: str, user_id: str) -> None:
        pdf = self._find_pdf(filename, self._get_pdfs_by_user(user_id))
        if pdf is not None:
            self._try_ingest(
                self._stored_path(pdf),
                pdf["filename"],
                user_id,
                bool(pdf["is_public"]),
            )

    def _try_ingest(
        self, file_path: Path, filename: str, user_id: str, is_public: bool
    ) -> None:
        try:
            chunks = self._parse_pdf(file_path)
            for chunk in chunks:
                chunk.metadata = {
                    "user_id": user_id,
                    "filename": filename,
                    "source": filename,
                    "is_public": int(is_public),
                }
            self._save_chunks(chunks)
            self._record_ingestion(filename, user_id, int(is_public))
        except Exception:
            logger.exception("Failed to ingest PDF %s", filename)

    def _stored_path(self, pdf: dict) -> Path:
        if pdf["is_public"]:
            return self._upload_directory / "data" / "public" / pdf["filename"]
        return self._upload_directory / "data" / Path(pdf["filepath"])

    @staticmethod
    def _find_pdf(filename: str, pdfs: list[dict]) -> dict | None:
        return next((pdf for pdf in pdfs if pdf["filename"] == filename), None)