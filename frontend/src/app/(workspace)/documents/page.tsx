"use client";

import { type ChangeEvent, useCallback, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/features/auth/auth-context";

type Pdf = { id: number; filename: string; filepath?: string; uploaded_by?: string; is_public?: number; is_indexed: boolean };
type UploadedPdf = Pick<Pdf, "id" | "filename" | "uploaded_by" | "is_public">;

export default function DocumentsPage() {
  const { auth, role } = useAuth();
  const [files, setFiles] = useState<Pdf[]>([]);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const loadFiles = useCallback(async () => {
    try {
      const fileResult = await apiRequest<{ pdfs: Pdf[] }>(role === "admin" ? "/admin/pdf" : "/user/pdf", auth);
      setFiles(fileResult.pdfs || []);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load documents.");
    }
  }, [auth, role]);

  useEffect(() => { void loadFiles(); }, [loadFiles]);

  async function ingestDocument(file: UploadedPdf) {
    let path: string;
    if (role === "admin") {
      path = file.is_public
        ? `/admin/vectordb/ingest/pdf/${file.id}/public`
        : `/admin/vectordb/ingest/pdf/${file.id}/private?user_id=${encodeURIComponent(file.uploaded_by || "admin")}`;
    } else {
      path = `/user/vectordb/ingest/pdf/${file.id}`;
    }
    await apiRequest(path, auth, { method: "POST" });
  }

  async function indexFile(file: Pdf) {
    setBusy(true); setError(""); setStatus(`Indexing ${file.filename}...`);
    try {
      await ingestDocument(file);
      setStatus(`${file.filename} is searchable now.`);
      await loadFiles();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not index document.");
    } finally {
      setBusy(false);
    }
  }

  async function uploadFiles(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files;
    if (!selected?.length) return;
    const form = new FormData();
    Array.from(selected).forEach((file) => form.append("files", file));
    form.append("is_public", role === "admin" ? "1" : "0");
    setBusy(true); setError(""); setStatus("");
    let uploaded: string[] = [];
    try {
      const result = await apiRequest<{ uploaded: string[]; uploaded_pdfs: UploadedPdf[]; errors?: { filename: string; error: string }[] }>(role === "admin" ? "/admin/pdf/upload" : "/user/pdf/upload", auth, { method: "POST", body: form });
      uploaded = result.uploaded || [];
      for (const [index, file] of result.uploaded_pdfs.entries()) {
        setStatus(`Uploaded ${uploaded.length} document(s). Indexing ${index + 1} of ${result.uploaded_pdfs.length}...`);
        await ingestDocument(file);
      }
      setStatus(`${uploaded.length} document(s) uploaded and indexed.`);
      if (result.errors?.length) {
        setError(result.errors.map((item) => `${item.filename || "PDF"}: ${item.error}`).join(" "));
      }
      await loadFiles();
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "Unknown error.";
      setError(uploaded.length
        ? `Uploaded ${uploaded.length} document(s), but indexing failed: ${message}`
        : `Upload failed: ${message}`);
      await loadFiles();
    } finally {
      setBusy(false);
      event.target.value = "";
    }
  }

  async function deleteFile(file: Pdf) {
    setError(""); setStatus("");
    try {
      await apiRequest(`${role === "admin" ? "/admin/pdf" : "/user/pdf"}/${file.id}`, auth, {
        method: "DELETE",
      });
      setStatus(`${file.filename} removed.`);
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
      <section className="grid documents-grid">
        <div className="panel card document-card">
          <h3>Add a source</h3><p>Upload PDF documents to make them available to the assistant.</p>
          <div className="upload"><strong>Choose documents</strong><br /><small className="subtle">PDF files are processed into searchable knowledge.</small><input type="file" accept="application/pdf,.pdf" multiple onChange={uploadFiles} disabled={busy} /></div>
        </div>
        <section className="panel card document-card">
          <h3>Stored documents</h3><p>Sources currently connected to this workspace.</p>
          <div className="list document-list">{files.length ? files.map((file) => {
            return <div className="list-row" key={`${file.id}-${file.filename}`}><div><strong>{file.filename}</strong><br /><small>{file.is_public ? "Shared" : "Private"}</small></div><div>{file.is_indexed ? <span className="subtle" aria-label="Document indexed">Indexed</span> : <button className="mini-button" onClick={() => void indexFile(file)} disabled={busy}>Index</button>} <button className="mini-button" onClick={() => void deleteFile(file)} disabled={busy}>Remove</button></div></div>;
          }) : <div className="subtle">No documents yet.</div>}</div>
        </section>
      </section>
    </>
  );
}