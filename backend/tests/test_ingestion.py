import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from app.application.pdf_ingestion import PdfIngestionService


class PdfIngestionTests(unittest.TestCase):
    def test_process_pdf_assigns_access_metadata_and_persists_chunks(self):
        document = SimpleNamespace(page_content="PDF text", metadata={})
        insert_chunks = Mock()
        record_ingestion = Mock()
        service = PdfIngestionService(
            upload_directory=Path("/tmp/uploads"),
            get_all_pdfs=lambda: [],
            get_pdfs_by_user=lambda user_id: [],
            parse_pdf=lambda file_path: [document],
            save_chunks=insert_chunks,
            record_ingestion=record_ingestion,
        )

        service._try_ingest(Path("report.pdf"), "report.pdf", "casey", False)

        self.assertEqual(
            document.metadata,
            {
                "user_id": "casey",
                "filename": "report.pdf",
                "source": "report.pdf",
                "is_public": 0,
            },
        )
        insert_chunks.assert_called_once_with([document])
        record_ingestion.assert_called_once_with("report.pdf", "casey", 0)


if __name__ == "__main__":
    unittest.main()