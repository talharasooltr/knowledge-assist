# Knowledge Assistant Frontend

This directory contains the Next.js web application for the Knowledge Assistant. It provides the sign-in experience, knowledge chat, document management, and administrator workspace.

## Local Development

If `frontend/node_modules` already has the dependencies, skip installation and start the server directly. `npm ci` downloads any uncached packages and replaces the contents of `node_modules`, so use it only for a fresh clone or disposable environment when network access is available.

```bash
cd frontend
npm run dev
```

The frontend is available at `http://localhost:4000`.

## Routes

- `/login` signs in members and administrators.
- `/chat` is the document-grounded chat workspace.
- `/documents` manages uploaded PDF files.
- `/admin/users` is available to administrators for user management.

Workspace routes share an authenticated layout, while each workflow has a dedicated page and URL. The root route redirects to `/chat`.

For a fresh clone, install exactly from the lockfile first:

```powershell
cd frontend
npm ci
npm run dev
```

`package-lock.json` pins the frontend dependency tree. Avoid `npm install` or `npm ci` when you want to preserve an existing `node_modules` directory or conserve bandwidth; routine local commands such as lint, type-check, build, and dev use the installed dependencies without installing packages.

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