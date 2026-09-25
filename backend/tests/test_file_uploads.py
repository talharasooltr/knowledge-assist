import io
import tempfile
import unittest
from pathlib import Path

from app.core.file_uploads import (
    InvalidPdfUploadError,
    UploadTooLargeError,
    save_pdf_stream,
)


class PdfUploadTests(unittest.TestCase):
    def test_streams_valid_pdf_within_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "valid.pdf"
            size = save_pdf_stream(io.BytesIO(b"%PDF-1.7\ncontent"), target, 64)

            self.assertEqual(size, len(b"%PDF-1.7\ncontent"))
            self.assertEqual(target.read_bytes(), b"%PDF-1.7\ncontent")

    def test_rejects_and_removes_oversized_partial_file(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "large.pdf"

            with self.assertRaises(UploadTooLargeError):
                save_pdf_stream(io.BytesIO(b"%PDF-" + b"x" * 100), target, 32)

            self.assertFalse(target.exists())

    def test_rejects_and_removes_file_without_pdf_signature(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "invalid.pdf"

            with self.assertRaises(InvalidPdfUploadError):
                save_pdf_stream(io.BytesIO(b"not a PDF"), target, 32)

            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()