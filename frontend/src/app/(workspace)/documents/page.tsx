"use client";

import { type ChangeEvent, useCallback, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/features/auth/auth-context";
import { PageHeader } from "@/components/page-header";

type Pdf = { id: number; filename: string; filepath?: string; uploaded_by?: string; is_public?: number; is_indexed: boolean };
type UploadedPdf = Pick<Pdf, "id" | "filename" | "uploaded_by" | "is_public">;

export default function DocumentsPage() {
  const { role } = useAuth();
  const [files, setFiles] = useState<Pdf[]>([]);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const loadFiles = useCallback(async () => {
    const result = await apiRequest<{ pdfs: Pdf[] }>("/pdf");
    return result.pdfs || [];
  }, []);

  useEffect(() => {
    let active = true;
    void loadFiles()
      .then((loadedFiles) => {
        if (active) setFiles(loadedFiles);
      })
      .catch((caught) => {
        if (active) setError(caught instanceof Error ? caught.message : "Could not load documents.");
      });
    return () => { active = false; };
  }, [loadFiles]);

  async function ingestDocument(file: UploadedPdf) {
    await apiRequest(`/vectordb/ingest/pdf/${file.id}`, { method: "POST" });
  }

  async function indexFile(file: Pdf) {
    setBusy(true); setError(""); setStatus(`Indexing ${file.filename}...`);
    try {
      await ingestDocument(file);
      setStatus(`${file.filename} is searchable now.`);
      setFiles(await loadFiles());
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
      const result = await apiRequest<{ uploaded: string[]; uploaded_pdfs: UploadedPdf[]; errors?: { filename: string; error: string }[] }>("/pdf/upload", { method: "POST", body: form });
      uploaded = result.uploaded || [];
      for (const [index, file] of result.uploaded_pdfs.entries()) {
        setStatus(`Uploaded ${uploaded.length} document(s). Indexing ${index + 1} of ${result.uploaded_pdfs.length}...`);
        await ingestDocument(file);
      }
      setStatus(`${uploaded.length} document(s) uploaded and indexed.`);
      if (result.errors?.length) {
        setError(result.errors.map((item) => `${item.filename || "PDF"}: ${item.error}`).join(" "));
      }
      setFiles(await loadFiles());
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "Unknown error.";
      setError(uploaded.length
        ? `Uploaded ${uploaded.length} document(s), but indexing failed: ${message}`
        : `Upload failed: ${message}`);
      setFiles(await loadFiles());
    } finally {
      setBusy(false);
      event.target.value = "";
    }
  }

  async function deleteFile(file: Pdf) {
    setError(""); setStatus("");
    try {
      await apiRequest(`/pdf/${file.id}`, {
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
      <PageHeader eyebrow="Workspace" title="Documents" description="Manage the sources behind your answers." />
      {error && <div className="error" role="alert">{error}</div>}
      {status && <div className="status" role="status">{status}</div>}
      <section className="grid documents-grid">
        <div className="panel card document-card">
          <h2 className="section-title">Add documents</h2><p>Upload PDFs to make them searchable.</p>
          <label className="upload">
            <span className="upload-symbol" aria-hidden="true">+</span>
            <strong>Choose PDF files</strong>
            <small>PDF · up to 20 MB per file</small>
            <input type="file" accept="application/pdf,.pdf" multiple onChange={uploadFiles} disabled={busy} />
          </label>
        </div>
        <section className="panel card document-card">
          <h2 className="section-title">Your library <span className="count">{files.length}</span></h2><p>Only your accessible documents appear here.</p>
          <div className="list document-list">{files.length ? files.map((file) => {
            return <div className="list-row" key={`${file.id}-${file.filename}`}><div className="document-name"><strong>{file.filename}</strong><small>{file.is_public ? "Shared" : "Private"}</small></div><div className="row-actions">{file.is_indexed ? <span className="state"><span className="state-dot" />Ready</span> : <button className="text-button" onClick={() => void indexFile(file)} disabled={busy}>Index</button>} <button className="text-button muted-button" onClick={() => void deleteFile(file)} disabled={busy}>Remove</button></div></div>;
          }) : <div className="empty-list">Your library is empty.</div>}</div>
        </section>
      </section>
    </>
  );
}