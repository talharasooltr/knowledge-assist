import logging
from pathlib import Path
from collections.abc import Callable

from langchain_core.documents import Document


logger = logging.getLogger(__name__)


class DocumentNotFoundError(LookupError):
    pass


class DocumentIngestionService:
    def __init__(
        self,
        upload_directory: Path,
        get_all_documents: Callable[[], list[dict]],
        get_documents_by_user: Callable[[str], list[dict]],
        parse_document: Callable[[Path], list[Document]],
        save_chunks: Callable[[list[Document]], bool],
        record_ingestion: Callable[[str, str, int, int | None], int],
    ) -> None:
        self._upload_directory = upload_directory
        self._get_all_documents = get_all_documents
        self._get_documents_by_user = get_documents_by_user
        self._parse_document = parse_document
        self._save_chunks = save_chunks
        self._record_ingestion = record_ingestion

    def ingest_all_public_documents(self) -> None:
        for document in self._get_all_documents():
            if document["is_public"] and not document["is_deleting"]:
                self._ingest_record(document, "public", True)

    def ingest_user_documents(self, user_id: str, public_only: bool = False) -> None:
        for document in self._get_documents_by_user(user_id):
            if document["is_deleting"] or (public_only and not document["is_public"]):
                continue
            self._ingest_record(document, user_id, bool(document["is_public"]))

    def ingest_document_by_id(
        self, pdf_id: int, user_id: str | None = None, is_public: bool | None = None
    ) -> None:
        document = next(
            (item for item in self._get_all_documents() if item["id"] == pdf_id),
            None,
        )
        if document is None or document["is_deleting"]:
            raise DocumentNotFoundError(f"Document with id {pdf_id} was not found.")
        target_user = user_id or ("public" if is_public else document["uploaded_by"])
        target_is_public = (
            bool(is_public) if is_public is not None else bool(document["is_public"])
        )
        self._ingest_record(document, target_user, target_is_public)

    def ingest_user_document_by_id(self, pdf_id: int, user_id: str) -> None:
        document = next(
            (item for item in self._get_documents_by_user(user_id) if item["id"] == pdf_id),
            None,
        )
        if document is None or document["is_deleting"]:
            raise DocumentNotFoundError(
                f"Document with id {pdf_id} was not found for this user."
            )
        self._ingest_record(document, user_id, bool(document["is_public"]))

    def _ingest_record(self, document: dict, user_id: str, is_public: bool) -> None:
        self._try_ingest(
            self._stored_path(document),
            document["filename"],
            user_id,
            is_public,
            document["id"],
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
            chunks = self._parse_document(file_path)
            for chunk in chunks:
                chunk.metadata = {
                    **(chunk.metadata or {}),
                    "user_id": user_id,
                    "filename": filename,
                    "source": filename,
                    "is_public": int(is_public),
                    "file_format": file_path.suffix.lstrip(".").lower(),
                }
                chunk.metadata["pdf_id"] = pdf_id
            self._save_chunks(chunks)
            self._record_ingestion(filename, user_id, int(is_public), pdf_id)
        except Exception:
            logger.exception("Failed to ingest document %s", filename)
            raise

    def _stored_path(self, document: dict) -> Path:
        return self._upload_directory / "data" / Path(document["filepath"])
