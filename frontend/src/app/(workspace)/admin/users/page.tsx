"use client";

import { type FormEvent, useCallback, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { PageHeader } from "@/components/page-header";

type User = { id: number; username: string };

export default function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);

  const loadUsers = useCallback(() => apiRequest<User[]>("/admin/users"), []);

  useEffect(() => {
    let active = true;
    void loadUsers()
      .then((loadedUsers) => {
        if (active) setUsers(loadedUsers);
      })
      .catch((caught) => {
        if (active) setError(caught instanceof Error ? caught.message : "Could not load users.");
      });
    return () => { active = false; };
  }, [loadUsers]);

  async function createUser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true); setError(""); setStatus("");
    try {
      const created = await apiRequest<User>("/admin/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.trim(), password }),
      });
      setStatus(`User ${created.username} was created.`);
      setUsername(""); setPassword("");
      setUsers(await loadUsers());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not create user.");
    } finally { setBusy(false); }
  }

  async function deleteUser(user: User) {
    if (!window.confirm(`Delete user ${user.username}?`)) return;
    setBusy(true); setError(""); setStatus("");
    try {
      await apiRequest(`/admin/users/${encodeURIComponent(user.username)}`, { method: "DELETE" });
      setStatus(`User ${user.username} was deleted.`);
      setUsers(await loadUsers());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not delete user.");
    } finally { setBusy(false); }
  }

  return (
    <>
      <PageHeader eyebrow="Administration" title="People" description="Manage access to this workspace." />
      {error && <div className="error" role="alert">{error}</div>}
      {status && <div className="status" role="status">{status}</div>}
      <section className="grid people-grid">
        <form className="panel card people-card" onSubmit={createUser}>
          <h2 className="section-title">Add a member</h2><p>Create an account for someone who needs access.</p>
          <div className="field"><label htmlFor="new-username">Username</label><input id="new-username" value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="off" required /></div>
          <div className="field"><label htmlFor="new-user-password">Temporary password</label><input id="new-user-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="new-password" required /></div>
          <button className="primary full" disabled={busy}>{busy ? "Creating..." : "Create user"}</button>
        </form>
        <section className="panel card people-card"><h2 className="section-title">Members <span className="count">{users.length}</span></h2><div className="list people-list">{users.length ? users.map((user) => <div className="list-row" key={user.id}><div className="document-name"><strong>{user.username}</strong><small>Member</small></div><button className="text-button muted-button" onClick={() => void deleteUser(user)} disabled={busy}>Remove</button></div>) : <div className="empty-list">No members yet.</div>}</div></section>
      </section>
    </>
  );
}