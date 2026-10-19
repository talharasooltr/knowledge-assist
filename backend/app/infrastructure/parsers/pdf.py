from pathlib import Path

from langchain_core.documents import Document

from app.infrastructure.parsers.documents import parse_document


def parse_pdf(file_path: Path) -> list[Document]:
    return parse_document(file_path)
