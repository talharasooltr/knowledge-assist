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
- User PDFs: `/user/pdf`, `/user/pdf/upload`, `/user/pdf/delete`
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
│   │   └── user/               # User HTTP endpoints
│   ├── application/            # Use cases and workflows
│   ├── core/                   # Configuration and cross-cutting concerns
│   └── infrastructure/
│       ├── db/                 # SQLAlchemy session, models, repositories
│       ├── providers/           # LLM and external AI provider adapters
│       └── retrieval/           # Vector search implementation
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

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key
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
- Test user isolation and permissions
- Verify PDF operations work correctly