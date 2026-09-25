"use client";

import { type FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth, type UserRole } from "@/features/auth/auth-context";

export default function LoginPage() {
  const router = useRouter();
  const { ready, signedIn, signIn } = useAuth();
  const [role, setRole] = useState<UserRole>("user");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (ready && signedIn) router.replace("/chat");
  }, [ready, router, signedIn]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      await signIn(role, username, password);
      router.replace("/chat");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to sign in.");
    } finally {
      setBusy(false);
    }
  }

  if (!ready || signedIn) return null;

  return (
    <main className="login-shell">
      <section className="login-aside">
        <div className="brand"><span className="brand-mark">◈</span> Knowledge Assistant</div>
        <div>
          <h1>All your knowledge, ready to answer.</h1>
          <p>Ask clear questions and get answers grounded in your documents.</p>
        </div>
        <div className="aside-note">A focused workspace for private and shared knowledge.</div>
      </section>
      <section className="login-panel">
        <form className="login-card" onSubmit={submit}>
          <h2>Welcome back</h2>
          <p>Sign in to your knowledge workspace.</p>
          <div className="role-toggle" aria-label="Account type">
            <button type="button" className={role === "user" ? "active" : ""} onClick={() => setRole("user")}>Member</button>
            <button type="button" className={role === "admin" ? "active" : ""} onClick={() => setRole("admin")}>Admin</button>
          </div>
          <div className="field">
            <label htmlFor="username">Username</label>
            <input id="username" value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" required />
          </div>
          <div className="field">
            <label htmlFor="password">Password</label>
            <input id="password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required />
          </div>
          {error && <div className="error" role="alert">{error}</div>}
          <button className="primary full" disabled={busy}>{busy ? "Signing in..." : "Sign in"}</button>
        </form>
      </section>
    </main>
  );
}