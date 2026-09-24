# RAG Chatbot with User Management

A Retrieval-Augmented Generation (RAG) chatbot system with user authentication, PDF management, and vector database integration using FastAPI, LangChain, and ChromaDB.

## Features

- **User Management**: Admin and regular user authentication
- **PDF Management**: Upload, ingest, and delete PDFs per user
- **Vector Database**: ChromaDB integration with metadata preservation
- **Chat Interface**: Interactive chat client with authentication

## Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key
- SQLite (included)
- ChromaDB (included)

### Local Setup

1. **From the repository root, create the shared virtual environment and install dependencies.** The `.venv` directory must remain at the repository root so it can be shared with the frontend.
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -r backend/requirements.txt
   ```

   Do not create a separate virtual environment inside `backend/`.

2. **Environment setup**
   ```sh
   mkdir data
   # Copy your PDF files into 'data' directory
   ```

3. **Create .env file**
   ```
   OPENAI_API_KEY=sk-proj-xxx
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=your_admin_password
   ```

4. **Start the server**
   ```sh
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

5. **Use the chat client**
   ```sh
   python Client/chat_client.py
   ```

## User Management

### Authentication

- **Admin Users**: Authenticated using environment variables
- **Regular Users**: Stored in SQLite database
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

### Authentication
- `POST /login` - User authentication
- `POST /admin/login` - Admin authentication

### User Management
- `GET /users` - List all users (admin only)
- `POST /users` - Create new user
- `PUT /users/{user_id}/password` - Reset user password (admin only)

### PDF Management
- `POST /upload/{user_id}` - Upload PDF for user
- `POST /ingest/{user_id}` - Ingest PDFs for user
- `DELETE /pdfs/{user_id}` - Delete all PDFs for user
- `DELETE /pdfs/{user_id}/{filename}` - Delete specific PDF

### Chat
- `POST /chat` - Chat with RAG system

## Project Structure

```
backend/
├── Client/
│   ├── admin_tools.py
│   ├── chat_client.py
│   ├── test_multi_chat.py
│   ├── user_tools.py
├── data/
│   ├── public/
│   │   └── ... (public PDFs)
│   ├── user_1/
│   │   └── ... (user_1's PDFs)
│   └── ... (other user folders)
├── Dockerfile
├── main.py
├── README.md
├── requirements.txt
├── routes/
│   ├── admin/
│   │   ├── admin_auth.py
│   │   ├── chat_manage.py
│   │   ├── data_manage.py
│   │   ├── user_manage.py
│   │   └── vectordb_manage.py
│   └── user/
│       ├── chat_manage.py
│       ├── data_manage.py
│       ├── user_auth.py
│       ├── user_manage.py
│       └── vectordb_manage.py
└── utils/
    ├── ingest.py
    ├── llm.py
    ├── vectordb.py
    └── sqlitedb.py
```

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key
- `ADMIN_USERNAME`: Admin username (default: admin)
- `ADMIN_PASSWORD`: Admin password

### Database
- **SQLite**: User management and PDF metadata
- **ChromaDB**: Vector embeddings storage

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify .env file exists with correct credentials
   - Check user exists in SQLite database

2. **PDF Upload Issues**
   - Ensure data directory exists
   - Check file permissions

3. **Vector Database Issues**
   - Clear chroma directory if corrupted
   - Re-ingest PDFs after clearing

### Useful Commands

```sh
# Clear vector database
python Client/memory_management.py --clear-vectors

# List all users
python Client/user_management.py --list-users

# Delete user PDFs
python Client/data_management.py --delete-user-pdfs USER_ID

# Admin operations
python Client/admin_tools.py --reset-password USER_ID

# User operations
python Client/user_tools.py --create-user USERNAME PASSWORD
```

## Development

### Adding New Features
1. Update API endpoints in `main.py`
2. Add corresponding client functions
3. Update database schema if needed
4. Test with multiple users

### Testing
- Test user isolation and permissions
- Verify PDF operations work correctly