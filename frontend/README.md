# Knowledge Assistant Frontend

This directory contains the Next.js web application for the Knowledge Assistant. It provides the sign-in experience, knowledge chat, document management, and administrator workspace.

## Local Development

From the repository root, install the frontend dependencies and start the development server:

```bash
cd frontend
npm install
npm run dev
```

The frontend is available at `http://localhost:4000`.

## Routes

- `/login` signs in members and administrators.
- `/chat` is the document-grounded chat workspace.
- `/documents` manages uploaded PDF files.
- `/admin/users` is available to administrators for user management.

Workspace routes share an authenticated layout, while each workflow has a dedicated page and URL. The root route redirects to `/chat`.

On Windows PowerShell, use the same commands:

```powershell
cd frontend
npm install
npm run dev
```

## Backend Connection

Set `NEXT_PUBLIC_BACKEND_URL` when the backend is not running at the default local address:

```env
NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000
```

The frontend uses the backend API for authentication, chat, document uploads, document management, and administrator user management.

## Production Build

```bash
npm run type-check
npm run build
```