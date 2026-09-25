from pathlib import Path
from typing import Callable


class PdfNotFoundError(LookupError):
    pass


class PdfStorageError(OSError):
    pass


class PdfDeletionPendingError(RuntimeError):
    pass


class PdfDeletionService:
    def __init__(
        self,
        storage_directory: Path,
        get_pdf_by_id: Callable[[int], dict | None],
        request_pdf_deletion: Callable[[int, str | None], bool],
        delete_pdf_by_id: Callable[[int, str | None], bool],
    ) -> None:
        self._storage_directory = storage_directory.resolve()
        self._get_pdf_by_id = get_pdf_by_id
        self._request_pdf_deletion = request_pdf_deletion
        self._delete_pdf_by_id = delete_pdf_by_id

    def delete_pdf(self, pdf_id: int, owner_id: str | None = None) -> dict:
        pdf = self._get_pdf_by_id(pdf_id)
        if pdf is None or (owner_id is not None and pdf["uploaded_by"] != owner_id):
            raise PdfNotFoundError(f"PDF {pdf_id} was not found.")

        relative_path = Path(pdf["filepath"])
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError("The stored PDF path is outside the upload directory.")
        file_path = self._storage_directory / relative_path
        if not file_path.parent.resolve().is_relative_to(self._storage_directory):
            raise ValueError("The stored PDF path is outside the upload directory.")

        if not pdf["is_deleting"] and not self._request_pdf_deletion(pdf_id, owner_id):
            raise PdfNotFoundError(f"PDF {pdf_id} was not found.")

        try:
            file_path.unlink(missing_ok=True)
        except OSError as error:
            raise PdfStorageError("Could not remove the stored PDF file.") from error

        if not self._delete_pdf_by_id(pdf_id, owner_id):
            raise PdfDeletionPendingError(
                f"PDF {pdf_id} is marked for deletion; retry the request to finish cleanup."
            )
        return pdf