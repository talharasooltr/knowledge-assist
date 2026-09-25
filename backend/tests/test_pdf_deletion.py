import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from app.application.pdf_deletion import PdfDeletionService, PdfNotFoundError


class PdfDeletionTests(unittest.TestCase):
    def test_deletes_by_id_and_removes_only_the_selected_file(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = Path(directory)
            target = storage / "casey" / "stored.pdf"
            target.parent.mkdir()
            target.write_bytes(b"pdf")
            pdf = {
                "id": 42,
                "filename": "same-name.pdf",
                "filepath": "casey/stored.pdf",
                "uploaded_by": "casey",
                "is_deleting": False,
            }
            request_deletion = Mock(return_value=True)
            delete_pdf = Mock(return_value=True)
            service = PdfDeletionService(
                storage,
                get_pdf_by_id=lambda pdf_id: pdf if pdf_id == 42 else None,
                request_pdf_deletion=request_deletion,
                delete_pdf_by_id=delete_pdf,
            )

            result = service.delete_pdf(42, "casey")

            self.assertEqual(result, pdf)
            self.assertFalse(target.exists())
            delete_pdf.assert_called_once_with(42, "casey")

    def test_rejects_paths_outside_storage_before_deleting_database_record(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = Path(directory) / "data"
            storage.mkdir()
            pdf = {
                "id": 42,
                "filename": "report.pdf",
                "filepath": "../outside.pdf",
                "uploaded_by": "casey",
                "is_deleting": False,
            }
            request_deletion = Mock(return_value=True)
            delete_pdf = Mock(return_value=True)
            service = PdfDeletionService(
                storage,
                get_pdf_by_id=lambda pdf_id: pdf,
                request_pdf_deletion=request_deletion,
                delete_pdf_by_id=delete_pdf,
            )

            with self.assertRaisesRegex(ValueError, "outside the upload directory"):
                service.delete_pdf(42, "casey")

            delete_pdf.assert_not_called()

    def test_user_cannot_delete_another_users_pdf(self):
        with tempfile.TemporaryDirectory() as directory:
            delete_pdf = Mock(return_value=True)
            service = PdfDeletionService(
                Path(directory),
                get_pdf_by_id=lambda pdf_id: {
                    "id": pdf_id,
                    "filename": "report.pdf",
                    "filepath": "casey/report.pdf",
                    "uploaded_by": "casey",
                    "is_deleting": False,
                },
                request_pdf_deletion=Mock(return_value=True),
                delete_pdf_by_id=delete_pdf,
            )

            with self.assertRaises(PdfNotFoundError):
                service.delete_pdf(42, "jordan")

            delete_pdf.assert_not_called()

    def test_storage_failure_keeps_database_record_for_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = Path(directory)
            target = storage / "casey" / "stored.pdf"
            target.mkdir(parents=True)
            delete_pdf = Mock(return_value=True)
            pdf = {
                "id": 42,
                "filename": "report.pdf",
                "filepath": "casey/stored.pdf",
                "uploaded_by": "casey",
                "is_deleting": False,
            }
            request_deletion = Mock(side_effect=lambda pdf_id, owner: pdf.update(is_deleting=True) or True)
            service = PdfDeletionService(
                storage,
                get_pdf_by_id=lambda pdf_id: pdf,
                request_pdf_deletion=request_deletion,
                delete_pdf_by_id=delete_pdf,
            )

            with self.assertRaises(OSError):
                service.delete_pdf(42, "casey")

            self.assertTrue(pdf["is_deleting"])
            delete_pdf.assert_not_called()

            target.rmdir()
            result = service.delete_pdf(42, "casey")

            self.assertEqual(result["id"], 42)
            request_deletion.assert_called_once_with(42, "casey")
            delete_pdf.assert_called_once_with(42, "casey")


if __name__ == "__main__":
    unittest.main()