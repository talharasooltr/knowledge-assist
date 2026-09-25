"use client";

import { type ChangeEvent, useCallback, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/features/auth/auth-context";

type Pdf = { id: number; filename: string; filepath?: string; uploaded_by?: string; is_public?: number };

export default function DocumentsPage() {
  const { auth, role } = useAuth();
  const [files, setFiles] = useState<Pdf[]>([]);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const loadFiles = useCallback(async () => {
    try {
      const result = await apiRequest<{ pdfs: Pdf[] }>(role === "admin" ? "/admin/pdf" : "/user/pdf", auth);
      setFiles(result.pdfs || []);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load documents.");
    }
  }, [auth, role]);

  useEffect(() => { void loadFiles(); }, [loadFiles]);

  async function uploadFiles(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files;
    if (!selected?.length) return;
    const form = new FormData();
    Array.from(selected).forEach((file) => form.append("files", file));
    form.append("is_public", role === "admin" ? "1" : "0");
    setBusy(true); setError(""); setStatus("");
    try {
      const result = await apiRequest<{ uploaded: string[] }>(role === "admin" ? "/admin/pdf/upload" : "/user/pdf/upload", auth, { method: "POST", body: form });
      setStatus(`${result.uploaded?.length || 0} document(s) uploaded.`);
      await loadFiles();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Upload failed.");
    } finally {
      setBusy(false);
      event.target.value = "";
    }
  }

  async function deleteFile(filename: string) {
    setError(""); setStatus("");
    try {
      await apiRequest(role === "admin" ? "/admin/pdf/delete" : "/user/pdf/delete", auth, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filenames: [filename] }),
      });
      setStatus(`${filename} removed.`);
      await loadFiles();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not remove that document.");
    }
  }

  return (
    <>
      <header className="topline"><div><div className="eyebrow">Knowledge workspace</div><h1>Your documents</h1><div className="subtle">Upload and manage the sources behind your answers.</div></div></header>
      {error && <div className="error" role="alert">{error}</div>}
      {status && <div className="status" role="status">{status}</div>}
      <section className="grid">
        <div className="panel card">
          <h3>Add a source</h3><p>Upload PDF documents to make them available to the assistant.</p>
          <div className="upload"><strong>Choose documents</strong><br /><small className="subtle">PDF files are processed into searchable knowledge.</small><input type="file" accept="application/pdf,.pdf" multiple onChange={uploadFiles} disabled={busy} /></div>
        </div>
        <section className="panel card">
          <h3>Stored documents</h3><p>Sources currently connected to this workspace.</p>
          <div className="list">{files.length ? files.map((file) => <div className="list-row" key={`${file.id}-${file.filename}`}><div><strong>{file.filename}</strong><br /><small>{file.is_public ? "Shared" : "Private"}</small></div><button className="mini-button" onClick={() => void deleteFile(file.filename)} disabled={busy}>Remove</button></div>) : <div className="subtle">No documents yet.</div>}</div>
        </section>
      </section>
    </>
  );
}