import io
import tempfile
import unittest
from pathlib import Path

from docx import Document

from app.core.file_uploads import (
    InvalidDocumentUploadError,
    InvalidPdfUploadError,
    UploadTooLargeError,
    save_document_stream,
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

    def test_accepts_a_valid_ooxml_document_signature(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "valid.docx"
            source = io.BytesIO()
            Document().save(source)
            content = source.getvalue()

            size = save_document_stream(
                io.BytesIO(content),
                target,
                1024 * 1024,
                ".docx",
            )

            self.assertEqual(size, len(content))
            self.assertEqual(target.read_bytes(), content)

    def test_rejects_a_zip_that_is_not_a_valid_office_document(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "invalid.docx"

            with self.assertRaises(InvalidDocumentUploadError):
                save_document_stream(
                    io.BytesIO(b"PK\x03\x04not an office document"),
                    target,
                    64,
                    ".docx",
                )

            self.assertFalse(target.exists())

    def test_rejects_document_with_mismatched_binary_signature(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "invalid.docx"

            with self.assertRaises(InvalidDocumentUploadError):
                save_document_stream(io.BytesIO(b"not a DOCX"), target, 64, ".docx")

            self.assertFalse(target.exists())

    def test_existing_destination_is_not_removed_on_collision(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "existing.txt"
            target.write_bytes(b"existing")

            with self.assertRaises(FileExistsError):
                save_document_stream(io.BytesIO(b"new contents"), target, 64, ".txt")

            self.assertEqual(target.read_bytes(), b"existing")


if __name__ == "__main__":
    unittest.main()