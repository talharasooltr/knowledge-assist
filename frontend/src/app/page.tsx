"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";

type Role = "user" | "admin";
type View = "chat" | "documents" | "users";
type Message = { role: "user" | "assistant"; content: string };
type Pdf = { id: number; filename: string; filepath?: string; uploaded_by?: string; is_public?: number };
type User = { id: number; username: string };

const API_URL = (process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

async function request(path: string, auth: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers);
  headers.set("Authorization", `Basic ${auth}`);
  return fetch(`${API_URL}${path}`, { ...options, headers });
}

function encodeAuth(username: string, password: string) {
  return btoa(`${username}:${password}`);
}

export default function KnowledgeAssistant() {
  const [auth, setAuth] = useState<string | null>(null);
  const [role, setRole] = useState<Role>("user");
  const [username, setUsername] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [view, setView] = useState<View>("chat");
  const [messages, setMessages] = useState<Message[]>([]);
  const [prompt, setPrompt] = useState("");
  const [files, setFiles] = useState<Pdf[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [newUsername, setNewUsername] = useState("");
  const [newUserPassword, setNewUserPassword] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const saved = window.sessionStorage.getItem("knowledge-auth");
    const savedRole = window.sessionStorage.getItem("knowledge-role") as Role | null;
    const savedName = window.sessionStorage.getItem("knowledge-user");
    if (saved && savedRole && savedName) {
      setAuth(saved);
      setRole(savedRole);
      setUsername(savedName);
    }
  }, []);

  useEffect(() => {
    if (auth && view === "documents") loadFiles();
    if (auth && role === "admin" && view === "users") loadUsers();
  }, [auth, view, role]);

  async function login(event: FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    const nextAuth = encodeAuth(username.trim(), loginPassword);
    try {
      const response = await request(`/${role}/auth/check`, nextAuth);
      if (!response.ok) throw new Error("The username or password is incorrect.");
      setAuth(nextAuth);
      window.sessionStorage.setItem("knowledge-auth", nextAuth);
      window.sessionStorage.setItem("knowledge-role", role);
      window.sessionStorage.setItem("knowledge-user", username.trim());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to sign in.");
    } finally { setBusy(false); }
  }

  function logout() {
    window.sessionStorage.clear();
    setAuth(null); setMessages([]); setView("chat");
  }

  async function sendMessage(event: FormEvent) {
    event.preventDefault();
    if (!auth || !prompt.trim()) return;
    const question = prompt.trim();
    setPrompt(""); setError(""); setMessages((current) => [...current, { role: "user", content: question }]);
    setBusy(true);
    try {
      const response = await request("/user/chat", auth, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ user_id: username, message: question }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "The assistant could not answer.");
      setMessages((current) => [...current, { role: "assistant", content: data.response || "No answer was returned." }]);
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Unable to reach the assistant."); }
    finally { setBusy(false); }
  }

  async function loadFiles() {
    if (!auth) return;
    const response = await request(role === "admin" ? "/admin/pdf" : "/user/pdf", auth);
    const data = await response.json();
    if (response.ok) setFiles(data.pdfs || []); else setError(data.detail || "Could not load documents.");
  }

  async function uploadFiles(event: ChangeEvent<HTMLInputElement>) {
    if (!auth || !event.target.files?.length) return;
    const form = new FormData();
    Array.from(event.target.files).forEach((file) => form.append("files", file));
    form.append("is_public", role === "admin" ? "1" : "0");
    setBusy(true); setError("");
    const response = await request(role === "admin" ? "/admin/pdf/upload" : "/user/pdf/upload", auth, { method: "POST", body: form });
    const data = await response.json();
    if (response.ok) { setStatus(`${data.uploaded?.length || 0} document(s) uploaded.`); loadFiles(); } else setError(data.detail || "Upload failed.");
    setBusy(false);
  }

  async function deleteFile(filename: string) {
    if (!auth) return;
    const response = await request(role === "admin" ? "/admin/pdf/delete" : "/user/pdf/delete", auth, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ filenames: [filename] }) });
    if (response.ok) { setStatus(`${filename} removed.`); loadFiles(); } else setError("Could not remove that document.");
  }

  async function loadUsers() {
    if (!auth) return;
    const response = await request("/admin/users", auth);
    const data = await response.json();
    if (response.ok) setUsers(data); else setError(data.detail || "Could not load users.");
  }

  async function createUser(event: FormEvent) {
    event.preventDefault();
    if (!auth || !newUsername.trim() || !newUserPassword) return;
    setBusy(true); setError(""); setStatus("");
    const response = await request("/admin/users", auth, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: newUsername.trim(), password: newUserPassword }),
    });
    const data = await response.json();
    if (response.ok) {
      setStatus(`User ${data.username} was created.`);
      setNewUsername(""); setNewUserPassword("");
      loadUsers();
    } else {
      setError(data.detail || "Could not create user.");
    }
    setBusy(false);
  }

  async function deleteUser(user: User) {
    if (!auth || !window.confirm(`Delete user ${user.username}?`)) return;
    setBusy(true); setError(""); setStatus("");
    const response = await request(`/admin/users/${encodeURIComponent(user.username)}`, auth, { method: "DELETE" });
    const data = await response.json();
    if (response.ok) { setStatus(`User ${user.username} was deleted.`); loadUsers(); }
    else setError(data.detail || "Could not delete user.");
    setBusy(false);
  }

  if (!auth) return <Login role={role} setRole={setRole} username={username} setUsername={setUsername} password={loginPassword} setPassword={setLoginPassword} onSubmit={login} error={error} busy={busy} />;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">◈</span> Knowledge Assistant</div>
        <div className="sidebar-user"><strong>{username}</strong><br />{role === "admin" ? "Administrator" : "Member"}</div>
        <nav className="nav">
          <button className={view === "chat" ? "active" : ""} onClick={() => setView("chat")}>Ask knowledge</button>
          <button className={view === "documents" ? "active" : ""} onClick={() => setView("documents")}>Documents</button>
          {role === "admin" && <button className={view === "users" ? "active" : ""} onClick={() => setView("users")}>People</button>}
        </nav>
        <button className="signout" onClick={logout}>Sign out</button>
      </aside>
      <main className="main">
        <div className="topline"><div><div className="eyebrow">Knowledge workspace</div><h1>{view === "chat" ? "Ask your knowledge" : view === "documents" ? "Your documents" : "People and access"}</h1><div className="subtle">{view === "chat" ? "Find answers across the information your team has collected." : view === "documents" ? "Upload and manage the sources behind your answers." : "Manage the people who can use this workspace."}</div></div></div>
        {error && <div className="error">{error}</div>}{status && <div className="status">{status}</div>}
        {view === "chat" && <section className="panel chat-panel"><div className="chat-list">{messages.length === 0 ? <div className="empty"><div><strong>What would you like to know?</strong>Ask a question about your indexed documents.</div></div> : messages.map((message, index) => <div className={`message ${message.role}`} key={`${message.role}-${index}`}>{message.content}</div>)}</div><form className="chat-form" onSubmit={sendMessage}><textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="Ask anything about your documents..." rows={1} /><button className="primary" disabled={busy}>{busy ? "Thinking" : "Ask"}</button></form></section>}
        {view === "documents" && <Documents files={files} onUpload={uploadFiles} onDelete={deleteFile} busy={busy} />}
        {view === "users" && <section className="grid"><form className="panel card" onSubmit={createUser}><h3>Create a user</h3><p>Add a member who can sign in to this workspace.</p><div className="field"><label htmlFor="new-username">Username</label><input id="new-username" value={newUsername} onChange={(event) => setNewUsername(event.target.value)} autoComplete="off" /></div><div className="field"><label htmlFor="new-user-password">Temporary password</label><input id="new-user-password" type="password" value={newUserPassword} onChange={(event) => setNewUserPassword(event.target.value)} autoComplete="new-password" /></div><button className="primary full" disabled={busy || !newUsername.trim() || !newUserPassword}>{busy ? "Creating..." : "Create user"}</button></form><section className="panel card"><h3>Workspace members</h3><div className="list">{users.map((user) => <div className="list-row" key={user.id}><div><strong>{user.username}</strong><br /><small>Member</small></div><button className="mini-button" onClick={() => deleteUser(user)} disabled={busy}>Delete</button></div>)}</div></section></section>}
      </main>
    </div>
  );
}

function Login({ role, setRole, username, setUsername, password, setPassword, onSubmit, error, busy }: { role: Role; setRole: (value: Role) => void; username: string; setUsername: (value: string) => void; password: string; setPassword: (value: string) => void; onSubmit: (event: FormEvent) => void; error: string; busy: boolean }) {
  return <main className="login-shell"><section className="login-aside"><div className="brand"><span className="brand-mark">◈</span> Knowledge Assistant</div><div><h1>All your knowledge, ready to answer.</h1><p>Bring together the documents and information your work depends on. Ask clear questions and get answers grounded in your sources.</p></div><div className="aside-note">A focused workspace for private and shared knowledge.</div></section><section className="login-panel"><form className="login-card" onSubmit={onSubmit}><h2>Welcome back</h2><p>Sign in to your knowledge workspace.</p><div className="role-toggle"><button type="button" className={role === "user" ? "active" : ""} onClick={() => setRole("user")}>Member</button><button type="button" className={role === "admin" ? "active" : ""} onClick={() => setRole("admin")}>Admin</button></div><div className="field"><label htmlFor="username">Username</label><input id="username" value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" /></div><div className="field"><label htmlFor="password">Password</label><input id="password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" /></div>{error && <div className="error">{error}</div>}<button className="primary full" disabled={busy}>{busy ? "Signing in..." : "Sign in"}</button></form></section></main>;
}

function Documents({ files, onUpload, onDelete, busy }: { files: Pdf[]; onUpload: (event: ChangeEvent<HTMLInputElement>) => void; onDelete: (filename: string) => void; busy: boolean }) {
  return <section className="grid"><div className="panel card"><h3>Add a source</h3><p>Upload PDF documents to make them available to the assistant.</p><div className="upload"><strong>Choose documents</strong><br /><small className="subtle">PDF files are processed into searchable knowledge.</small><input type="file" accept=".pdf" multiple onChange={onUpload} disabled={busy} /></div></div><div className="panel card"><h3>Stored documents</h3><p>Sources currently connected to this workspace.</p><div className="list">{files.length ? files.map((file) => <div className="list-row" key={`${file.id}-${file.filename}`}><div><strong>{file.filename}</strong><br /><small>{file.is_public ? "Shared" : "Private"}</small></div><button className="mini-button" onClick={() => onDelete(file.filename)}>Remove</button></div>) : <div className="subtle">No documents yet.</div>}</div></div></section>;
}
