# Knowledge Assistant

Knowledge Assistant is a document-grounded chat application. The backend supports PDF, DOCX, PPTX, XLSX, TXT, Markdown, CSV/TSV, JSON, and HTML upload, ingestion, hybrid search, and chat over uploaded documents. Images, web pages, URLs, audio, OCR, and legacy binary Office files are future extensions, not currently implemented ingestion sources.

Users can upload supported documents and ask natural-language questions to retrieve relevant content and generate RAG-powered answers.

The platform provides separate experiences for regular users and administrators. Users can add and explore knowledge, while administrators can manage users, shared content, access, and system activity.

## Screenshots

The screenshots below show the PDF workflow using the fictional Maple Court Resident Guide demo document.

### Indexed Documents

PDFs are listed with their indexing status after upload.

![Documents page showing indexed PDFs](docs/screenshots/01-indexed-pdf.png)

### Cited Answer

An after-hours leak question answered from the guide, with the source filename and page citation visible.

![Chat answer with PDF citation](docs/screenshots/02-cited-answer.png)

### Citation Verification

The cited answer is shown alongside the matching source page for manual verification.

![Answer beside the cited source page](docs/screenshots/03-source-page.png)

### Missing Information

When asked about a pet policy that is not covered in the guide, the assistant says it cannot confirm the answer from the available documents.

![Assistant response when the PDF does not contain the answer](docs/screenshots/04-not-in-document.png)

## What It Does

- **Manage document knowledge**: Upload, ingest, list, and remove common document formats.
- **Hybrid search**: Combine PostgreSQL full-text search with pgvector similarity over token-aware, structure-preserving chunks.
- **Ask grounded questions**: Retrieve relevant document content and cite page ranges or sections in chat responses.
- **Keep conversations separate**: Create multiple chats with independent histories and retrieval context.
- **Separate private and shared content**: Apply user/public metadata to document retrieval.
- **Manage users and chat history**: Provide separate user and administrator API operations.

## Who It Is For

Knowledge Assistant is useful for teams and individuals who need question answering over PDF collections, including research and internal document assistance.

## How It Works

1. Upload a supported document through the API or frontend.
2. Ingest it through a format-specific extractor, normalize its structure, split text into token-aware chunks, and create embeddings.
3. Ask a question in natural language.
4. The backend retrieves relevant chunks and passes them to the configured chat model.

## Architecture

The root diagram shows the main runtime and data flows. The [backend README](backend/README.md) documents the backend layers and implementation details.

```mermaid
flowchart LR
    user([User or administrator]) --> web[Next.js web app]
    web -->|Session-authenticated API requests| api[FastAPI API]

    subgraph ingestion["Document ingestion"]
        api --> upload[Validate and store upload]
        upload -->|Original file| files[(Document file storage)]
        upload --> parser[Format-specific parsers]
        parser --> chunks[Normalize structure and create token-aware chunks]
        chunks --> embed[Embedding provider]
        embed -->|Chunk embeddings| db[(PostgreSQL)]
    end

    subgraph chat["Grounded chat"]
        api --> question[Question and conversation]
        question --> queryEmbed[Embed question]
        queryEmbed --> retrieval[Hybrid retrieval<br/>pgvector + full-text, fused with RRF]
        db -->|Relevant chunks| retrieval
        retrieval --> context[Context with source locations]
        context --> model[Chat model provider]
        model --> answer[Grounded answer with citations]
        answer --> api
    end

    api <-->|Users, sessions, conversations,<br/>document metadata and chunks| db
```

The embedding and chat model providers can be configured for OpenAI or Azure OpenAI. PostgreSQL stores both vector embeddings and the full-text search index used during retrieval.

## Project Areas

```
.
├── backend/
│   ├── README.md
│   └── ... (application services and knowledge processing)
│
├── frontend/
│   ├── README.md
│   └── ... (user and administrator workspace)
│
```

## Technical Documentation

- [Backend README](backend/README.md): Backend setup, authentication, content management, database, ingestion, retrieval, and API details.
- [Frontend README](frontend/README.md): Next.js user workspace, frontend setup, API connection, and production build details.
