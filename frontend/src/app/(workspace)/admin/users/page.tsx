"use client";

import { type FormEvent, useCallback, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/features/auth/auth-context";

type User = { id: number; username: string };

export default function AdminUsersPage() {
  const { auth } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);

  const loadUsers = useCallback(async () => {
    try { setUsers(await apiRequest<User[]>("/admin/users", auth)); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Could not load users."); }
  }, [auth]);

  useEffect(() => { void loadUsers(); }, [loadUsers]);

  async function createUser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true); setError(""); setStatus("");
    try {
      const created = await apiRequest<User>("/admin/users", auth, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.trim(), password }),
      });
      setStatus(`User ${created.username} was created.`);
      setUsername(""); setPassword("");
      await loadUsers();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not create user.");
    } finally { setBusy(false); }
  }

  async function deleteUser(user: User) {
    if (!window.confirm(`Delete user ${user.username}?`)) return;
    setBusy(true); setError(""); setStatus("");
    try {
      await apiRequest(`/admin/users/${encodeURIComponent(user.username)}`, auth, { method: "DELETE" });
      setStatus(`User ${user.username} was deleted.`);
      await loadUsers();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not delete user.");
    } finally { setBusy(false); }
  }

  return (
    <>
      <header className="topline"><div><div className="eyebrow">Administration</div><h1>People and access</h1><div className="subtle">Manage the people who can use this workspace.</div></div></header>
      {error && <div className="error" role="alert">{error}</div>}
      {status && <div className="status" role="status">{status}</div>}
      <section className="grid people-grid">
        <form className="panel card people-card" onSubmit={createUser}>
          <h3>Create a user</h3><p>Add a member who can sign in to this workspace.</p>
          <div className="field"><label htmlFor="new-username">Username</label><input id="new-username" value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="off" required /></div>
          <div className="field"><label htmlFor="new-user-password">Temporary password</label><input id="new-user-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="new-password" required /></div>
          <button className="primary full" disabled={busy}>{busy ? "Creating..." : "Create user"}</button>
        </form>
        <section className="panel card people-card"><h3>Workspace members</h3><div className="list people-list">{users.map((user) => <div className="list-row" key={user.id}><div><strong>{user.username}</strong><br /><small>Member</small></div><button className="mini-button" onClick={() => void deleteUser(user)} disabled={busy}>Delete</button></div>)}</div></section>
      </section>
    </>
  );
}