"use client";

import { type ChangeEvent, useCallback, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/features/auth/auth-context";
import { PageHeader } from "@/components/page-header";

type WorkspaceDocument = { id: number; filename: string; filepath?: string; uploaded_by?: string; is_public?: number; is_indexed: boolean };
type UploadedDocument = Pick<WorkspaceDocument, "id" | "filename" | "uploaded_by" | "is_public">;

export default function DocumentsPage() {
  const { role } = useAuth();
  const [files, setFiles] = useState<WorkspaceDocument[]>([]);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const loadFiles = useCallback(async () => {
    const result = await apiRequest<{ documents: WorkspaceDocument[] }>("/documents");
    return result.documents || [];
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

  async function ingestDocument(file: UploadedDocument) {
    await apiRequest(`/vectordb/ingest/document/${file.id}`, { method: "POST" });
  }

  async function indexFile(file: WorkspaceDocument) {
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
      const result = await apiRequest<{
        uploaded: string[];
        uploaded_documents: UploadedDocument[];
        errors?: { filename: string; error: string }[];
      }>("/documents/upload", { method: "POST", body: form });
      uploaded = result.uploaded || [];
      let indexed = 0;
      const processingErrors = (result.errors ?? [])
        .map((item) => `${item.filename || "Document"}: ${item.error}`);
      for (const [index, file] of result.uploaded_documents.entries()) {
        setStatus(`Uploaded ${uploaded.length} document(s). Indexing ${index + 1} of ${result.uploaded_documents.length}...`);
        try {
          await ingestDocument(file);
          indexed += 1;
        } catch (caught) {
          const message = caught instanceof Error ? caught.message : "Could not index this document.";
          processingErrors.push(`${file.filename}: ${message}`);
        }
      }
      setStatus(`${indexed} of ${result.uploaded_documents.length} document(s) indexed.`);
      try {
        setFiles(await loadFiles());
      } catch (caught) {
        const message = caught instanceof Error ? caught.message : "Could not refresh the document list.";
        processingErrors.push(message);
      }
      setError(processingErrors.join(" "));
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "Unknown error.";
      setError(uploaded.length
        ? `Uploaded ${uploaded.length} document(s), but processing failed: ${message}`
        : `Upload failed: ${message}`);
      try {
        setFiles(await loadFiles());
      } catch (refreshError) {
        const refreshMessage = refreshError instanceof Error
          ? refreshError.message
          : "Could not refresh the document list.";
        setError((current) => `${current} ${refreshMessage}`);
      }
    } finally {
      setBusy(false);
      event.target.value = "";
    }
  }

  async function deleteFile(file: WorkspaceDocument) {
    setError(""); setStatus("");
    try {
      await apiRequest(`/documents/${file.id}`, {
        method: "DELETE",
      });
      setStatus(`${file.filename} removed.`);
      setFiles(await loadFiles());
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
          <h2 className="section-title">Add documents</h2><p>Upload supported documents to make them searchable.</p>
          <label className="upload">
            <span className="upload-symbol" aria-hidden="true">+</span>
            <strong>Choose document files</strong>
            <small>PDF, DOCX, PPTX, XLSX, TXT, MD, CSV/TSV, JSON, HTML · up to 20 MB each</small>
            <input
              type="file"
              accept=".pdf,.docx,.pptx,.xlsx,.txt,.md,.markdown,.csv,.tsv,.json,.html,.htm"
              multiple
              onChange={uploadFiles}
              disabled={busy}
            />
          </label>
        </div>
        <section className="panel card document-card">
          <h2 className="section-title">Your library <span className="count">{files.length}</span></h2><p>Only your accessible documents appear here.</p>
          <div className="list document-list">{files.length ? files.map((file) => {
            return <div className="list-row" key={`${file.id}-${file.filename}`}><div className="document-name"><strong>{file.filename}</strong><small>{file.is_public ? "Shared" : "Private"}</small></div><div className="row-actions">{file.is_indexed && <span className="state"><span className="state-dot" />Ready</span>} <button className="text-button" onClick={() => void indexFile(file)} disabled={busy}>{file.is_indexed ? "Reindex" : "Index"}</button> <button className="text-button muted-button" onClick={() => void deleteFile(file)} disabled={busy}>Remove</button></div></div>;
          }) : <div className="empty-list">Your library is empty.</div>}</div>
        </section>
      </section>
    </>
  );
}