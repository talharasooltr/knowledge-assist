from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)


def parse_pdf(file_path: Path) -> list[Document]:
    return _splitter.split_documents(PyPDFLoader(file_path).load())