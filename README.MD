# Knowledge Assistant

Multi-source AI knowledge assistant for document ingestion, semantic search, and RAG-powered question answering.

The application consists of a FastAPI backend and a Streamlit frontend.

For local development, use one shared `.venv` located at the repository root. Both the backend and frontend use this same virtual environment; do not create separate virtual environments inside `backend/` or `frontend/`.

## Project Structure

```
.
├── backend/
│   ├── README.md
│   └── ... (FastAPI API and RAG services)
│
├── frontend/
│   ├── README.md
│   └── ... (Streamlit interface)
│
```

## Features

* **Dual User Roles**: Separate interfaces and permissions for regular Users and Admins.
* **User Management**: Admins can add, delete, and manage user credentials.
* **Data Management**: Users and Admins can upload and manage PDF documents.
* **VectorDB Integration**: Uploaded documents can be ingested into a vector database for RAG.
* **Interactive Chat**: Users can chat with the RAG model, which utilizes the ingested documents.

## Technical Documentation

- [Backend README](backend/README.md): API, authentication, document management, RAG services, configuration, and backend development.
- [Frontend README](frontend/README.md): Streamlit interface, frontend configuration, and local development.
