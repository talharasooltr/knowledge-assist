import unittest
from pathlib import Path
from unittest.mock import Mock

from langchain_core.documents import Document

from app.application.document_ingestion import DocumentIngestionService


class DocumentIngestionTests(unittest.TestCase):
    def test_process_document_assigns_access_metadata_and_persists_chunks(self):
        document = Document(page_content="document text", metadata={})
        insert_chunks = Mock()
        record_ingestion = Mock()
        service = DocumentIngestionService(
            upload_directory=Path("/tmp/uploads"),
            get_all_documents=lambda: [],
            get_documents_by_user=lambda user_id: [],
            parse_document=lambda file_path: [document],
            save_chunks=insert_chunks,
            record_ingestion=record_ingestion,
        )

        service._try_ingest(Path("report.pdf"), "report.pdf", "casey", False, 42)

        self.assertEqual(
            document.metadata,
            {
                "user_id": "casey",
                "filename": "report.pdf",
                "source": "report.pdf",
                "is_public": 0,
                "file_format": "pdf",
                "pdf_id": 42,
            },
        )
        insert_chunks.assert_called_once_with([document])
        record_ingestion.assert_called_once_with("report.pdf", "casey", 0, 42)

    def test_ingestion_errors_are_propagated(self):
        service = DocumentIngestionService(
            upload_directory=Path("/tmp/uploads"),
            get_all_documents=lambda: [],
            get_documents_by_user=lambda user_id: [],
            parse_document=Mock(side_effect=RuntimeError("Embedding failed")),
            save_chunks=Mock(),
            record_ingestion=Mock(),
        )

        with self.assertRaisesRegex(RuntimeError, "Embedding failed"):
            service._try_ingest(Path("report.pdf"), "report.pdf", "casey", False, 42)

    def test_ingest_by_document_id_preserves_identity_for_duplicate_filenames(self):
        document = Document(page_content="PDF text", metadata={})
        pdf = {
            "id": 42,
            "filename": "report.pdf",
            "filepath": "casey/unique.pdf",
            "uploaded_by": "casey",
            "is_public": 0,
            "is_deleting": False,
        }
        save_chunks = Mock()
        record_ingestion = Mock()
        parse_document = Mock(return_value=[document])
        service = DocumentIngestionService(
            upload_directory=Path("/tmp/uploads"),
            get_all_documents=lambda: [pdf, {**pdf, "id": 43, "filepath": "other/unique.pdf"}],
            get_documents_by_user=lambda user_id: [pdf, {**pdf, "id": 43, "filepath": "casey/another.pdf"}],
            parse_document=parse_document,
            save_chunks=save_chunks,
            record_ingestion=record_ingestion,
        )

        service.ingest_user_document_by_id(42, "casey")

        parse_document.assert_called_once_with(Path("/tmp/uploads/data/casey/unique.pdf"))
        self.assertEqual(document.metadata["pdf_id"], 42)
        self.assertEqual(document.metadata["file_format"], "pdf")
        save_chunks.assert_called_once_with([document])
        record_ingestion.assert_called_once_with("report.pdf", "casey", 0, 42)


if __name__ == "__main__":
    unittest.main()