"use client";

import { type FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/features/auth/auth-context";
import Link from "next/link";

export default function LoginPage() {
  const router = useRouter();
  const { ready, signedIn, signIn, error: authError } = useAuth();
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
      await signIn(username, password);
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
      <section className="login-content">
        <Link className="brand login-brand" href="/login">
          <span className="brand-mark" aria-hidden="true">K</span>
          <span>Knowledge Assistant</span>
        </Link>
        <div className="login-intro">
          <div className="eyebrow">Your knowledge workspace</div>
          <h1>Answers grounded in your documents.</h1>
          <p>Ask a question. See where the answer came from.</p>
        </div>
        <form className="login-card" onSubmit={submit}>
          <div className="login-card-heading">
            <h2>Sign in</h2>
            <p>Continue to your workspace.</p>
          </div>
          <div className="field">
            <label htmlFor="username">Username</label>
            <input id="username" value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" required />
          </div>
          <div className="field">
            <label htmlFor="password">Password</label>
            <input id="password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required />
          </div>
          {(error || authError) && <div className="error" role="alert">{error || authError}</div>}
          <button className="primary full" disabled={busy}>{busy ? "Signing in..." : "Sign in"}</button>
        </form>
      </section>
    </main>
  );
}