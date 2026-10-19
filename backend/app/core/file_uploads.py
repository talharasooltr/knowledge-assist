from pathlib import Path
from typing import BinaryIO
from zipfile import BadZipFile, ZipFile

from app.core.document_formats import DOCUMENT_SIGNATURES

_OOXML_REQUIRED_ENTRIES = {
    ".docx": "word/document.xml",
    ".pptx": "ppt/presentation.xml",
    ".xlsx": "xl/workbook.xml",
}
_MAX_ARCHIVE_ENTRIES = 10_000
_MAX_UNCOMPRESSED_ARCHIVE_BYTES = 200 * 1024 * 1024

class UploadTooLargeError(ValueError):
    pass


class InvalidDocumentUploadError(ValueError):
    pass


InvalidPdfUploadError = InvalidDocumentUploadError


def save_document_stream(
    source: BinaryIO,
    destination: Path,
    max_bytes: int,
    extension: str,
) -> int:
    total_bytes = 0
    first_chunk = True
    created_file = False
    try:
        with destination.open("xb") as output:
            created_file = True
            while chunk := source.read(1024 * 1024):
                if first_chunk:
                    first_chunk = False
                    signature = DOCUMENT_SIGNATURES.get(extension)
                    if signature is not None and not chunk.startswith(signature):
                        raise InvalidDocumentUploadError(
                            f"The uploaded file does not match its {extension} extension."
                        )
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    raise UploadTooLargeError(
                        f"Document exceeds the {max_bytes}-byte upload limit."
                    )
                output.write(chunk)
            if first_chunk:
                raise InvalidDocumentUploadError("The uploaded document is empty.")
        if extension in _OOXML_REQUIRED_ENTRIES:
            _validate_ooxml_archive(destination, extension)
        return total_bytes
    except Exception:
        if created_file:
            destination.unlink(missing_ok=True)
        raise


def save_pdf_stream(source: BinaryIO, destination: Path, max_bytes: int) -> int:
    return save_document_stream(source, destination, max_bytes, ".pdf")


def _validate_ooxml_archive(path: Path, extension: str) -> None:
    try:
        with ZipFile(path) as archive:
            entries = archive.infolist()
            if len(entries) > _MAX_ARCHIVE_ENTRIES:
                raise InvalidDocumentUploadError(
                    "Office document contains too many archive entries."
                )
            if sum(entry.file_size for entry in entries) > _MAX_UNCOMPRESSED_ARCHIVE_BYTES:
                raise InvalidDocumentUploadError("Office document expands beyond the allowed size.")
            if any(entry.flag_bits & 1 for entry in entries):
                raise InvalidDocumentUploadError("Encrypted Office documents are not supported.")
            if _OOXML_REQUIRED_ENTRIES[extension] not in archive.namelist():
                raise InvalidDocumentUploadError(
                    f"The uploaded archive is not a valid {extension} document."
                )
    except BadZipFile as error:
        raise InvalidDocumentUploadError(
            f"The uploaded archive is not a valid {extension} document."
        ) from error