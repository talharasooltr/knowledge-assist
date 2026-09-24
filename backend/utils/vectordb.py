from dotenv import load_dotenv
import os
import uuid
import time
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import (
    OpenAIEmbeddings,
    AzureOpenAIEmbeddings,
)
from langchain_core.documents import Document


# ============================================================
# Environment
# ============================================================

load_dotenv()


# ============================================================
# LLM / Embedding Provider
# ============================================================

LLM_PROVIDER = os.getenv(
    "LLM_PROVIDER",
    "openai"
).strip().lower()


if LLM_PROVIDER not in {"openai", "azure-openai"}:
    raise ValueError(
        "Invalid LLM_PROVIDER. "
        "Use either 'openai' or 'azure-openai'."
    )


# ============================================================
# Embeddings
# ============================================================

if LLM_PROVIDER == "openai":

    embedding = OpenAIEmbeddings()

else:

    embedding = AzureOpenAIEmbeddings(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv(
            "AZURE_OPENAI_API_VERSION",
            "2024-10-21"
        ),
    )


# ============================================================
# Text Splitter
# ============================================================

splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50
)


CHAT_HISTORY_LIMIT = 10


# ============================================================
# Cross-platform persistent directories
# ============================================================

# Current file:
#
# backend/
# ├── main.py
# ├── routes/
# ├── utils/
# │   └── vectordb.py
# └── chroma/
#
# Default Chroma location:
#
# backend/chroma/
#
# This works on Windows and Linux.

BASE_DIR = Path(__file__).resolve().parent.parent


DEFAULT_PERSIST_DIR = BASE_DIR / "chroma"


# .env can override this:
#
# PERSIST_DIR=/some/path/chroma
#
# Windows:
# PERSIST_DIR=C:/some/path/chroma

PERSIST_DIR = Path(
    os.getenv(
        "PERSIST_DIR",
        str(DEFAULT_PERSIST_DIR)
    )
).expanduser()


PERSIST_DIR.mkdir(
    parents=True,
    exist_ok=True
)


CHROMA_MEMORY_DIR = PERSIST_DIR / "chroma_memory"
CHROMA_PDF_DIR = PERSIST_DIR / "chroma_pdf"


CHROMA_MEMORY_DIR.mkdir(
    parents=True,
    exist_ok=True
)

CHROMA_PDF_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# Helper
# ============================================================

def get_embedding():
    """
    Return the configured embedding model.
    """

    return embedding


# ============================================================
# User message history embedding
# ============================================================

def save_user_message(user_id, message):

    db = Chroma(
        collection_name=f"user_{user_id}",
        embedding_function=embedding,
        persist_directory=str(CHROMA_MEMORY_DIR)
    )

    # Fetch all existing messages
    all_docs = db.get()

    all_ids = all_docs["ids"]
    all_metadatas = all_docs["metadatas"]

    # Sort by timestamp
    docs_with_time = []

    for idx, meta in enumerate(all_metadatas):

        meta = meta or {}

        ts = meta.get(
            "timestamp",
            0
        )

        docs_with_time.append(
            (
                all_ids[idx],
                ts
            )
        )

    docs_with_time.sort(
        key=lambda x: x[1]
    )

    # Keep only CHAT_HISTORY_LIMIT messages
    if len(docs_with_time) >= CHAT_HISTORY_LIMIT:

        num_to_delete = (
            len(docs_with_time)
            - (CHAT_HISTORY_LIMIT - 1)
        )

        ids_to_delete = [
            doc[0]
            for doc in docs_with_time[
                :num_to_delete
            ]
        ]

        db.delete(
            ids=ids_to_delete
        )

    # Add new message
    now = time.time()

    doc = Document(
        page_content=message,
        metadata={
            "user_id": user_id,
            "timestamp": now
        }
    )

    db.add_documents(
        [doc],
        ids=[str(uuid.uuid4())]
    )


def retrieve_user_memory(
    user_id,
    query,
    k=3
):

    db = Chroma(
        collection_name=f"user_{user_id}",
        embedding_function=embedding,
        persist_directory=str(CHROMA_MEMORY_DIR)
    )

    results = db.similarity_search(
        query,
        k=k
    )

    # Remove empty documents
    filtered_results = [
        doc
        for doc in results
        if getattr(
            doc,
            "page_content",
            None
        )
    ]

    return filtered_results


def get_all_history(user_id):

    db = Chroma(
        collection_name=f"user_{user_id}",
        embedding_function=embedding,
        persist_directory=str(CHROMA_MEMORY_DIR)
    )

    all_docs = db.get()

    docs = []

    for i, doc in enumerate(
        all_docs["documents"]
    ):

        meta = (
            all_docs["metadatas"][i]
            or {}
        )

        ts = meta.get(
            "timestamp",
            0
        )

        docs.append(
            (
                ts,
                doc
            )
        )

    # Oldest -> newest
    docs.sort(
        key=lambda x: x[0]
    )

    return [
        doc
        for ts, doc in docs
    ]


def clear_history_by_user(user_id):

    db = Chroma(
        collection_name=f"user_{user_id}",
        embedding_function=embedding,
        persist_directory=str(CHROMA_MEMORY_DIR)
    )

    db.delete_collection()


def clear_history_all():

    client = Chroma(
        persist_directory=str(CHROMA_MEMORY_DIR),
        embedding_function=None
    )._client

    for col in client.list_collections():

        db = Chroma(
            collection_name=col.name,
            embedding_function=embedding,
            persist_directory=str(CHROMA_MEMORY_DIR)
        )

        db.delete_collection()


# ============================================================
# PDF embedding
# ============================================================

def insert_new_chunks(chunks):

    db = Chroma(
        persist_directory=str(CHROMA_PDF_DIR),
        embedding_function=embedding
    )

    ids = [
        str(uuid.uuid4())
        for _ in chunks
    ]

    db.add_documents(
        chunks,
        ids=ids
    )

    return True


def get_available_user_ids():

    import re

    client = Chroma(
        persist_directory=str(CHROMA_MEMORY_DIR),
        embedding_function=None
    )._client

    user_ids = []

    for col in client.list_collections():

        match = re.match(
            r"user_(.+)",
            col.name
        )

        if match:
            user_ids.append(
                match.group(1)
            )

    return user_ids


def get_pdf_sources():

    db = Chroma(
        persist_directory=str(CHROMA_PDF_DIR),
        embedding_function=embedding
    )

    all_docs = db.get()

    sources = set()

    for meta in all_docs["metadatas"]:

        meta = meta or {}

        if (
            "source" in meta
            and "user_id" in meta
        ):

            sources.add(
                (
                    meta["source"],
                    meta["user_id"]
                )
            )

    return [
        {
            "source": source,
            "ingested_by": user_id
        }
        for source, user_id in sources
    ]


def retrieve_pdf_for_user(
    user_id,
    query,
    k=3
):

    db = Chroma(
        persist_directory=str(CHROMA_PDF_DIR),
        embedding_function=embedding
    )

    all_docs = db.get()

    # Filter:
    #
    # User's own PDFs
    # OR
    # Public PDFs

    filtered_docs = []

    for i, meta in enumerate(
        all_docs["metadatas"]
    ):

        meta = meta or {}

        if (
            meta.get("user_id") == user_id
            or meta.get("is_public") == 1
        ):

            doc_text = all_docs[
                "documents"
            ][i]

            filtered_docs.append(
                Document(
                    page_content=doc_text,
                    metadata=meta
                )
            )

    if not filtered_docs:
        return []

    # Temporary Chroma collection
    temp_db = Chroma.from_documents(
        filtered_docs,
        embedding=embedding
    )

    results = temp_db.similarity_search(
        query,
        k=k
    )

    return results


def clear_pdf_by_source(
    source_name
):

    """
    Delete all vector chunks for
    a specific PDF source.

    Matches either:
        metadata["source"]

    or:
        metadata["filename"]
    """

    db = Chroma(
        persist_directory=str(CHROMA_PDF_DIR),
        embedding_function=embedding
    )

    all_docs = db.get()

    ids_to_delete = []

    for i, meta in enumerate(
        all_docs["metadatas"]
    ):

        meta = meta or {}

        if (
            meta.get("source") == source_name
            or meta.get("filename") == source_name
        ):

            ids_to_delete.append(
                all_docs["ids"][i]
            )

    if ids_to_delete:

        db.delete(
            ids=ids_to_delete
        )


def clear_pdf_by_user(
    user_id
):

    """
    Delete all PDF vector chunks
    belonging to the specified user.
    """

    db = Chroma(
        persist_directory=str(CHROMA_PDF_DIR),
        embedding_function=embedding
    )

    all_docs = db.get()

    ids_to_delete = []

    for i, meta in enumerate(
        all_docs["metadatas"]
    ):

        meta = meta or {}

        if meta.get(
            "user_id"
        ) == user_id:

            ids_to_delete.append(
                all_docs["ids"][i]
            )

    if ids_to_delete:

        db.delete(
            ids=ids_to_delete
        )


def clear_all_pdf():

    client = Chroma(
        persist_directory=str(CHROMA_PDF_DIR),
        embedding_function=None
    )._client

    for col in client.list_collections():

        db = Chroma(
            collection_name=col.name,
            embedding_function=embedding,
            persist_directory=str(CHROMA_PDF_DIR)
        )

        db.delete_collection()


# ============================================================
# Debug / Test
# ============================================================

if __name__ == "__main__":

    print("=== Vectordb Test ===")

    print()
    print(
        "LLM_PROVIDER:",
        LLM_PROVIDER
    )

    print()
    print(
        "Persistent directory:"
    )

    print(
        PERSIST_DIR.resolve()
    )

    print()
    print(
        "Memory directory:"
    )

    print(
        CHROMA_MEMORY_DIR.resolve()
    )

    print()
    print(
        "PDF directory:"
    )

    print(
        CHROMA_PDF_DIR.resolve()
    )

    # --------------------------------------------------------
    # Test user message history
    # --------------------------------------------------------

    test_user = "testuser"

    print()
    print(
        f"Saving messages for user: {test_user}"
    )

    save_user_message(
        test_user,
        "Hello, this is the first message."
    )

    save_user_message(
        test_user,
        "This is a follow-up message."
    )

    save_user_message(
        test_user,
        "Another message about AI."
    )

    print()
    print(
        "All history:",
        get_all_history(test_user)
    )

    print()
    print(
        "Memory search for 'AI':",
        retrieve_user_memory(
            test_user,
            "AI",
            k=2
        )
    )

    print()
    print(
        "Clearing user history..."
    )

    clear_history_by_user(
        test_user
    )

    print()
    print(
        "All history after clear:",
        get_all_history(test_user)
    )

    # --------------------------------------------------------
    # Test PDF embedding
    # --------------------------------------------------------

    print()
    print(
        "Inserting PDF chunks..."
    )

    chunks = [

        Document(
            page_content=(
                "This is a PDF chunk about machine learning."
            ),
            metadata={
                "user_id": test_user,
                "filename": "ml.pdf",
                "source": "ml.pdf",
                "is_public": 0
            }
        ),

        Document(
            page_content=(
                "This is a public PDF chunk about AI."
            ),
            metadata={
                "user_id": "otheruser",
                "filename": "ai.pdf",
                "source": "ai.pdf",
                "is_public": 1
            }
        )

    ]

    insert_new_chunks(
        chunks
    )

    print()
    print(
        "PDF sources:",
        get_pdf_sources()
    )

    print()
    print(
        "Retrieve PDF for user "
        "(should get both public and own):"
    )

    print(
        retrieve_pdf_for_user(
            test_user,
            "AI",
            k=2
        )
    )

    print()
    print(
        "Clearing PDF by source 'ml.pdf'..."
    )

    clear_pdf_by_source(
        "ml.pdf"
    )

    print()
    print(
        "Retrieve PDF for user after clear by source:"
    )

    print(
        retrieve_pdf_for_user(
            test_user,
            "machine",
            k=2
        )
    )

    print()
    print(
        "Clearing all PDF data..."
    )

    clear_all_pdf()

    print()
    print(
        "Retrieve PDF for user after clear all:"
    )

    print(
        retrieve_pdf_for_user(
            test_user,
            "AI",
            k=2
        )
    )

    print()
    print(
        "=== Test Complete ==="
    )