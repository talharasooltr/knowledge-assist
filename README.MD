# Knowledge Assistant

Knowledge Assistant is a multi-source AI workspace that helps people collect knowledge from PDFs, images, web pages, URLs, and audio, then ask questions and receive answers grounded in that knowledge.

Instead of searching through every source manually, users can bring their information into one place and use natural-language questions to find relevant content, compare information, and generate RAG-powered answers.

The platform provides separate experiences for regular users and administrators. Users can add and explore knowledge, while administrators can manage users, shared content, access, and system activity.

## What It Does

- **Collect knowledge from many sources**: Bring together PDFs, images, web pages, URLs, and audio in one knowledge workspace.
- **Understand and organize content**: Convert source content into information that can be searched by meaning, not only by exact keywords.
- **Answer questions with context**: Ask questions in natural language and receive answers based on the content you have provided.
- **Keep answers connected to sources**: Use the relevant documents and source content behind an answer to make the results easier to review.
- **Support private and shared knowledge**: Keep personal content separated while allowing administrators to manage public or shared resources.
- **Manage knowledge over time**: Upload, process, review, and remove content as the knowledge base changes.

## Who It Is For

Knowledge Assistant is useful for teams and individuals who need to work with information spread across documents, media, and online sources. It can support research, internal knowledge sharing, document-based assistance, and question answering over a growing collection of content.

## How It Works

1. Add information from one or more supported sources.
2. The assistant processes and organizes the content.
3. Ask a question in everyday language.
4. The assistant finds the most relevant context and generates an answer using that context.

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
- [Frontend README](frontend/README.md): User workspace, Streamlit interface, frontend setup, and backend connection details.
