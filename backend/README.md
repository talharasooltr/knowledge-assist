# Knowledge Assistant Backend

A PDF-based Retrieval-Augmented Generation (RAG) API using FastAPI, LangChain, PostgreSQL, SQLAlchemy, and pgvector. PDF is the currently implemented ingestion source; other media sources are not implemented yet.

## Features

- **User Management**: Admin and regular user authentication
- **PDF Management**: Upload, ingest, list, and delete PDFs
- **Vector Search**: PostgreSQL with pgvector and metadata-based access control
- **Chat API**: Authenticated chat endpoints used by the Next.js frontend

## Quick Start

### Prerequisites

- Python 3.10+
- OpenAI or Azure OpenAI credentials
- PostgreSQL 15+ with the `vector` extension

### Local Setup

1. **From the repository root, create the shared virtual environment and install dependencies.** The `.venv` directory should remain at the repository root so the backend and frontend tools share one environment location.
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -r backend/requirements.txt
   ```

   On Windows PowerShell, activate the same root environment with:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r backend\requirements.txt
   ```

   Do not create a separate virtual environment inside `backend/`.

2. **Configure the backend environment.** Copy `backend/.env.example` to `backend/.env` and set the required values. The configuration loader reads this file directly.

   ```sh
   cp backend/.env.example backend/.env
   ```

3. **Start PostgreSQL** and create the application database. The migration enables the `vector` extension, so the database role must have permission to create it (or the extension must already be installed).

   Set `DATABASE_URL` to the connection URL for your database. `UPLOADS_DIR` defaults to the repository root, where uploads are stored under `data/`.

   Create the database before running migrations if it does not exist:
   ```sh
   createdb -h localhost -U postgres knowledge_assistant
   ```

   Apply the PostgreSQL schema from any directory:
   ```sh
   .venv/bin/alembic -c backend/alembic.ini upgrade head
   ```

   From PowerShell, use the equivalent path syntax:
   ```powershell
   .venv\Scripts\alembic.exe -c backend\alembic.ini upgrade head
   ```

4. **Start the server**
   ```sh
   .venv/bin/uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
   ```

5. **Use the chat client**
   ```sh
   .venv/bin/python backend/clients/chat_client.py
   ```

## User Management

### Authentication

- **Admin Users**: Authenticated using environment variables
- **Regular Users**: Stored in PostgreSQL
- **Session Management**: Credentials required for each operation

### User Operations

- **Admin Functions**:
  - View all users
  - Reset user passwords
  - Manage all PDFs
  - Clear vector database

- **Regular User Functions**:
  - Upload PDFs
  - Ingest PDFs manually
  - Chat with their documents
  - Delete their own PDFs

## PDF Management

### Upload and Ingestion

1. **Upload PDFs**: Files are stored in user-specific directories
2. **Manual Ingestion**: Process PDFs to create vector embeddings
3. **Metadata Preservation**: User information stored with embeddings

### File Operations

- Upload PDFs to user directory
- Ingest PDFs to vector database
- Delete PDFs (files + database records + embeddings)
- Clear all vector embeddings

## API Endpoints

The interactive API reference is available at `http://localhost:8000/docs` when the server is running. Main endpoint groups are:

- Authentication: `/user/auth/check`, `/user/login`, `/admin/auth/check`
- User PDFs: `GET /user/pdf`, `POST /user/pdf/upload`, `DELETE /user/pdf/{pdf_id}`
- Admin PDFs: `GET /admin/pdf`, `POST /admin/pdf/upload`, `DELETE /admin/pdf/{pdf_id}`, `DELETE /admin/pdf/public`
- PDF ingestion uses stable IDs: `/user/vectordb/ingest/pdf/{pdf_id}` and `/admin/vectordb/ingest/pdf/{pdf_id}/...`
- Configure unique `ADMIN_USERNAME` and `ADMIN_PASSWORD` values; startup authentication fails closed if either is missing.
- `MAX_PDF_UPLOAD_BYTES` defaults to 20 MiB per PDF. Production deployments should also enforce request-size limits and HTTPS at the reverse proxy.
- Set `CORS_ALLOWED_ORIGINS` to the exact frontend origins for the deployment; do not use wildcard origins with credentials.
- User ingestion and retrieval management: `/user/vectordb/...`
- User chat and history: `/user/chat`, `/user/chat/history`
- Admin users, PDFs, ingestion, and chat history: `/admin/...`

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application and router registration
│   ├── api/
│   │   ├── admin/              # Admin HTTP endpoints
│   │   ├── user/               # User HTTP endpoints
│   │   └── dependencies.py     # FastAPI dependency wiring
│   ├── application/            # Use cases, independent of FastAPI
│   ├── core/                   # Configuration and cross-cutting concerns
│   ├── schemas/                # HTTP request and response models
│   └── infrastructure/
│       ├── db/                 # SQLAlchemy session, models, repositories
│       ├── parsers/            # File-format parsing adapters
│       ├── providers/          # Chat and embedding provider adapters
│       └── retrieval/          # Chat memory and PDF vector persistence
├── clients/                    # CLI and API helper clients
│   ├── admin_tools.py
│   ├── chat_client.py
│   ├── user_tools.py
├── scripts/                    # Operational and maintenance scripts
├── tests/                      # Integration and load tests
│   └── load_test_chat.py
├── alembic/                    # Database migrations
├── alembic.ini
├── requirements.txt
└── README.md
```

Run commands from the repository root. Python imports use the `app` package;
the API entrypoint is `app.main:app`.

### Code Organization Rules

- `api/` translates HTTP requests, applies authentication dependencies, and returns HTTP responses.
- `application/` coordinates use cases and should not import FastAPI or SQLAlchemy models.
- `infrastructure/` implements database, vector search, file parsing, and AI-provider details.
- `schemas/` contains API input/output models shared by routes.
- Dependencies point inward: API may call application services; application defines what it needs; infrastructure supplies concrete implementations.
- Add tests beside the appropriate `tests/` grouping. Keep network and database dependencies mocked in unit tests.

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key
- `LLM_PROVIDER`: `openai` or `azure-openai`
- `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, and `AZURE_OPENAI_API_VERSION`: Azure OpenAI resource configuration
- `AZURE_OPENAI_CHAT_DEPLOYMENT`: Exact Azure chat deployment name; required when `LLM_PROVIDER=azure-openai`
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`: Exact Azure embedding deployment name; required when `LLM_PROVIDER=azure-openai`
- `ADMIN_USERNAME`: Admin username (default: admin)
- `ADMIN_PASSWORD`: Admin password
- `DATABASE_URL`: PostgreSQL connection URL
- `EMBEDDING_DIMENSION`: Embedding vector dimension; must match the configured model

### Database
- **PostgreSQL**: Users, PDFs, ingestion state, chat memory, and PDF chunks
- **pgvector**: Embeddings stored in PostgreSQL `vector` columns

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify .env file exists with correct credentials
   - Check the user exists in PostgreSQL

2. **PDF Upload Issues**
   - Ensure data directory exists
   - Check file permissions

3. **Vector Search Issues**
   - Verify PostgreSQL is running and the `vector` extension is enabled
   - Verify `DATABASE_URL` and `EMBEDDING_DIMENSION`
   - Re-ingest PDFs after changing the embedding model

### Useful Commands

```sh
# Run the database summary script
PYTHONPATH=backend .venv/bin/python backend/scripts/database_summary.py

# Run the chat load test against a running API
PYTHONPATH=backend .venv/bin/python backend/tests/load_test_chat.py
```

## Development

### Adding New Features
1. Add or update a router under `app/api/` and register it in `app/main.py`.
2. Put reusable workflows in `app/application/` rather than implementing them in route handlers.
3. Put persistence and external integrations under `app/infrastructure/`.
4. Update database migrations and tests when schemas or behavior change.

### Testing
- Run unit tests with `.venv/bin/python -m unittest discover -s backend/tests -v`.
- Test user isolation and permissions.
- Verify PDF upload, ingestion, and retrieval behavior against PostgreSQL in integration tests.