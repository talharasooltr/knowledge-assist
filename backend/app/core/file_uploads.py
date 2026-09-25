from pathlib import Path
from typing import BinaryIO


class UploadTooLargeError(ValueError):
    pass


class InvalidPdfUploadError(ValueError):
    pass


def save_pdf_stream(source: BinaryIO, destination: Path, max_bytes: int) -> int:
    total_bytes = 0
    first_chunk = True
    try:
        with destination.open("xb") as output:
            while chunk := source.read(1024 * 1024):
                if first_chunk:
                    first_chunk = False
                    if not chunk.startswith(b"%PDF-"):
                        raise InvalidPdfUploadError("The uploaded file is not a valid PDF.")
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    raise UploadTooLargeError(
                        f"PDF exceeds the {max_bytes}-byte upload limit."
                    )
                output.write(chunk)
            if first_chunk:
                raise InvalidPdfUploadError("The uploaded PDF is empty.")
        return total_bytes
    except Exception:
        destination.unlink(missing_ok=True)
        raise